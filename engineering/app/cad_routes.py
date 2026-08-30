from __future__ import annotations

import base64
import binascii
import gzip
import io
import tempfile
from pathlib import Path
import re
import hashlib
import numpy as np

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .cad_kernel import extract_step, OCC_AVAILABLE, cq
from .storage import StorageConfigurationError, put_bytes, require_durable_storage, configured as storage_configured

router = APIRouter(prefix="/v1/geometry", tags=["cad"])
MAX_STEP_BYTES = 25_000_000
MAX_COMPRESSED_BYTES = 10_000_000

class EnclosureRequest(BaseModel):
    width_mm: float = Field(gt=1, le=1000)
    depth_mm: float = Field(gt=1, le=1000)
    height_mm: float = Field(gt=1, le=1000)
    wall_mm: float = Field(gt=0.6, le=20)
    clearance_mm: float = Field(ge=0, le=10, default=0.25)
    mounting_hole_diameter_mm: float = Field(gt=0, le=20, default=2.4)
    mounting_hole_inset_mm: float = Field(gt=0, le=100, default=5)
    revision: str = Field(min_length=1, max_length=20, default="A")
    material: str = Field(min_length=1, max_length=100, default="PETG")


def _bounded_gzip_decode(encoded: str) -> bytes:
    try: packed = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc: raise HTTPException(422, "file_base64_gzip is not valid base64") from exc
    if len(packed) > MAX_COMPRESSED_BYTES: raise HTTPException(413, "compressed STEP payload exceeds 10 MB limit")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(packed), mode="rb") as stream: raw = stream.read(MAX_STEP_BYTES + 1)
    except (EOFError, gzip.BadGzipFile, OSError) as exc: raise HTTPException(422, "file_base64_gzip is not valid gzip-compressed base64") from exc
    if len(raw) > MAX_STEP_BYTES: raise HTTPException(413, "decompressed STEP payload exceeds 25 MB limit")
    return raw

async def _read_step_request(request: Request) -> tuple[str, bytes]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form(); upload = form.get("file")
        if upload is None or not hasattr(upload, "read"): raise HTTPException(422, "Multipart STEP request must contain a file field")
        name = getattr(upload, "filename", None) or "model.step"; raw = await upload.read(MAX_STEP_BYTES + 1)
        if len(raw) > MAX_STEP_BYTES: raise HTTPException(413, "Geometry exceeds 25 MB limit")
    elif content_type.startswith("application/json"):
        try: body = await request.json()
        except Exception as exc: raise HTTPException(400, "Malformed JSON request") from exc
        if not isinstance(body, dict): raise HTTPException(422, "JSON STEP request must be an object")
        name = str(body.get("filename") or "model.step"); encoded = body.get("file_base64"); compressed = body.get("file_base64_gzip")
        if isinstance(encoded, str) and encoded:
            try: raw = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc: raise HTTPException(422, "file_base64 is not valid base64") from exc
        elif isinstance(compressed, str) and compressed: raw = _bounded_gzip_decode(compressed)
        else: raise HTTPException(422, "JSON STEP request must contain file_base64 or file_base64_gzip")
        if len(raw) > MAX_STEP_BYTES: raise HTTPException(413, "Geometry exceeds 25 MB limit")
    else: raise HTTPException(415, "STEP endpoint accepts multipart/form-data or application/json")
    if not name.lower().endswith((".step", ".stp")): raise HTTPException(415, "Only STEP/STP is accepted")
    if not raw: raise HTTPException(422, "Empty STEP file")
    return Path(name).name, raw


def _validate_generated_step(raw: bytes, filename: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="fabrient-generated-step-") as d:
        path = Path(d) / filename; path.write_bytes(raw); validation = extract_step(str(path))
    if validation.get("status") != "validated":
        raise HTTPException(422, f"Generated STEP failed kernel round-trip validation: {validation.get('reason', 'unknown error')}")
    return validation


def _persist_step(raw: bytes) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    try:
        require_durable_storage()
        if not storage_configured():
            return {"mode": "inline", "durable": False}
        ref = put_bytes(prefix="cad/generated", data=raw, content_type="application/step", sha256=digest)
        return {"mode": "object_storage", "durable": True, "object_key": ref.key, "download_url": ref.download_url, "size_bytes": ref.size_bytes, "sha256": ref.sha256}
    except StorageConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc

@router.post("/generate")
def generate_enclosure(x: EnclosureRequest):
    if not OCC_AVAILABLE or cq is None: raise HTTPException(503, "OCCT/CadQuery runtime is unavailable; CAD generation is disabled rather than approximated.")
    if x.wall_mm * 2 + x.clearance_mm >= min(x.width_mm, x.depth_mm): raise HTTPException(422, "Wall and clearance consume the available enclosure footprint.")
    if x.mounting_hole_inset_mm * 2 >= min(x.width_mm, x.depth_mm): raise HTTPException(422, "Mounting-hole inset is too large for the enclosure.")
    try:
        outer = cq.Workplane("XY").box(x.width_mm, x.depth_mm, x.height_mm, centered=(False, False, False))
        inner = cq.Workplane("XY").box(x.width_mm-2*x.wall_mm, x.depth_mm-2*x.wall_mm, max(x.height_mm-x.wall_mm, x.wall_mm), centered=(False, False, False)).translate((x.wall_mm, x.wall_mm, x.wall_mm))
        enclosure = outer.cut(inner)
        hole_r = x.mounting_hole_diameter_mm / 2
        positions = [(x.mounting_hole_inset_mm, x.mounting_hole_inset_mm), (x.width_mm-x.mounting_hole_inset_mm, x.mounting_hole_inset_mm), (x.width_mm-x.mounting_hole_inset_mm, x.depth_mm-x.mounting_hole_inset_mm), (x.mounting_hole_inset_mm, x.depth_mm-x.mounting_hole_inset_mm)]
        for px, py in positions:
            tool = cq.Workplane("XY").center(px, py).circle(hole_r).extrude(x.wall_mm + 2)
            enclosure = enclosure.cut(tool)
        with tempfile.TemporaryDirectory(prefix="fabrient-cad-") as d:
            path = Path(d) / f"enclosure-r{x.revision}.step"
            cq.exporters.export(enclosure, str(path), exportType="STEP")
            raw = path.read_bytes()
        if not raw or len(raw) > MAX_STEP_BYTES: raise HTTPException(500, "Generated STEP is empty or exceeds the supported release size.")
        validation = _validate_generated_step(raw, path.name)
        storage = _persist_step(raw)
        response = {"status":"validated", "format":"STEP", "filename":path.name, "size_bytes":len(raw), "parameters":x.model_dump(), "validation":validation, "provenance":{"generator":"CadQuery/OCCT", "generation":"deterministic-parametric", "round_trip":"required", "synthetic_measurements":False}, "storage":storage}
        if storage["mode"] == "inline": response["step_base64"] = base64.b64encode(raw).decode("ascii")
        return response
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, f"Deterministic CAD generation failed: {exc}") from exc

@router.post("/step")
async def step_geometry(request: Request):
    name, raw = await _read_step_request(request)
    with tempfile.TemporaryDirectory(prefix="fabrient-step-") as d:
        path = Path(d) / name; path.write_bytes(raw); result = extract_step(str(path))
    if result.get("status") == "error":
        text = raw.decode("utf-8", errors="ignore"); points=[]
        pattern=r"CARTESIAN_POINT\s*\([^;]*?\(\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*\)\s*\)"
        for match in re.finditer(pattern,text,re.I|re.S): points.append(tuple(float(v) for v in match.groups()))
        if not points: raise HTTPException(422,result.get("reason","STEP extraction failed"))
        arr=np.asarray(points,dtype=float); mins,maxs=arr.min(axis=0),arr.max(axis=0)
        result={"status":"limited","units":"unknown_source_units","point_count":len(points),"bounding_box":{"min":mins.tolist(),"max":maxs.tolist(),"size":(maxs-mins).tolist()},"feature_extraction":{"method":"Cartesian-point fallback","topology_features":None,"status":"limited"},"provenance":{"source":"STEP","method":"kernel failed; bounded Cartesian-point fallback","warning":"Full B-rep topology and unit declaration were not inferred."}}
    result.setdefault("feature_extraction",{"status":"limited","method":"kernel result without explicit feature extraction"}); result.setdefault("filename",name); result.setdefault("file_size_bytes",len(raw)); result.setdefault("provenance",{}); result["provenance"]["synthetic"]=False; result["provenance"]["visualization"]="kernel-derived tessellation"
    return result
