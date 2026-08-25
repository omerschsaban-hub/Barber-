from __future__ import annotations

import base64
import binascii
import gzip
import io
import tempfile
from pathlib import Path
import re
import numpy as np

from fastapi import APIRouter, HTTPException, Request

from .cad_kernel import extract_step

router = APIRouter(prefix="/v1/geometry", tags=["cad"])
MAX_STEP_BYTES = 25_000_000
MAX_COMPRESSED_BYTES = 10_000_000


def _bounded_gzip_decode(encoded: str) -> bytes:
    try:
        packed = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(422, "file_base64_gzip is not valid base64") from exc
    if len(packed) > MAX_COMPRESSED_BYTES:
        raise HTTPException(413, "compressed STEP payload exceeds 10 MB limit")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(packed), mode="rb") as stream:
            raw = stream.read(MAX_STEP_BYTES + 1)
    except (EOFError, gzip.BadGzipFile, OSError) as exc:
        raise HTTPException(422, "file_base64_gzip is not valid gzip-compressed base64") from exc
    if len(raw) > MAX_STEP_BYTES:
        raise HTTPException(413, "decompressed STEP payload exceeds 25 MB limit")
    return raw


async def _read_step_request(request: Request) -> tuple[str, bytes]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(422, "Multipart STEP request must contain a file field")
        name = getattr(upload, "filename", None) or "model.step"
        raw = await upload.read(MAX_STEP_BYTES + 1)
        if len(raw) > MAX_STEP_BYTES:
            raise HTTPException(413, "Geometry exceeds 25 MB limit")
    elif content_type.startswith("application/json"):
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(400, "Malformed JSON request") from exc
        if not isinstance(body, dict):
            raise HTTPException(422, "JSON STEP request must be an object")
        name = str(body.get("filename") or "model.step")
        encoded = body.get("file_base64")
        compressed = body.get("file_base64_gzip")
        if isinstance(encoded, str) and encoded:
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(422, "file_base64 is not valid base64") from exc
            if len(raw) > MAX_STEP_BYTES:
                raise HTTPException(413, "Geometry exceeds 25 MB limit")
        elif isinstance(compressed, str) and compressed:
            raw = _bounded_gzip_decode(compressed)
        else:
            raise HTTPException(422, "JSON STEP request must contain file_base64 or file_base64_gzip")
    else:
        raise HTTPException(415, "STEP endpoint accepts multipart/form-data or application/json with file_base64/file_base64_gzip")

    if not name.lower().endswith((".step", ".stp")):
        raise HTTPException(415, "Only STEP/STP is accepted")
    if len(raw) == 0:
        raise HTTPException(422, "Empty STEP file")
    if len(raw) > MAX_STEP_BYTES:
        raise HTTPException(413, "Geometry exceeds 25 MB limit")
    return Path(name).name, raw


@router.post("/step")
async def step_geometry(request: Request):
    name, raw = await _read_step_request(request)
    with tempfile.TemporaryDirectory(prefix="fabrient-step-") as d:
        path = Path(d) / name
        path.write_bytes(raw)
        result = extract_step(str(path))
    if result.get("status") == "error":
        text = raw.decode("utf-8", errors="ignore")
        points = []
        pattern = r"CARTESIAN_POINT\s*\([^;]*?\(\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*\)\s*\)"
        for match in re.finditer(pattern, text, re.I | re.S):
            points.append(tuple(float(v) for v in match.groups()))
        if not points:
            raise HTTPException(422, result.get("reason", "STEP extraction failed"))
        arr = np.asarray(points, dtype=float)
        mins, maxs = arr.min(axis=0), arr.max(axis=0)
        result = {
            "status": "limited",
            "units": "unknown_source_units",
            "point_count": len(points),
            "bounding_box": {"min": mins.tolist(), "max": maxs.tolist(), "size": (maxs-mins).tolist()},
            "feature_extraction": {"method": "Cartesian-point fallback", "topology_features": None, "status": "limited"},
            "provenance": {"source": "STEP", "method": "kernel failed; bounded Cartesian-point fallback", "warning": "Full B-rep topology and unit declaration were not inferred."},
        }
    result.setdefault("feature_extraction", {"status": "limited", "method": "kernel result without explicit feature extraction"})
    result.setdefault("filename", name)
    result.setdefault("file_size_bytes", len(raw))
    result.setdefault("provenance", {})
    result["provenance"]["synthetic"] = False
    result["provenance"]["visualization"] = "kernel-derived tessellation"
    return result
