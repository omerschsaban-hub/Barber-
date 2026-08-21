from __future__ import annotations

import base64
import binascii
import tempfile
from pathlib import Path
import re
import numpy as np

from fastapi import APIRouter, HTTPException, Request

from .cad_kernel import extract_step

router = APIRouter(prefix="/v1/geometry", tags=["cad"])
MAX_STEP_BYTES = 25_000_000


async def _read_step_request(request: Request) -> tuple[str, bytes]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(422, "Multipart STEP request must contain a file field")
        name = getattr(upload, "filename", None) or "model.step"
        raw = await upload.read()
    elif content_type.startswith("application/json"):
        body = await request.json()
        name = str(body.get("filename") or "model.step")
        encoded = body.get("file_base64")
        if isinstance(encoded, str) and encoded:
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(422, "file_base64 is not valid base64") from exc
        else:
            # Some MCP/file bridges surface an attached file as a local path instead
            # of bytes. Accept that bridge form at the engine boundary and immediately
            # materialize the bytes here. Never infer or synthesize geometry.
            file_path = body.get("file_path")
            if not isinstance(file_path, str) or not file_path:
                raise HTTPException(422, "JSON STEP request must contain file_base64 or file_path")
            path = Path(file_path)
            if not path.is_file():
                raise HTTPException(422, "file_path does not resolve to a readable file in the engineering runtime")
            name = str(body.get("filename") or path.name)
            raw = path.read_bytes()
    else:
        raise HTTPException(415, "STEP endpoint accepts multipart/form-data or application/json with file_base64/file_path")

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
        # A syntactically valid/minimal STEP file may not contain enough topology for
        # the kernel. Fall back to a bounded Cartesian-point envelope rather than
        # pretending the file is invalid or inventing B-rep topology.
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
            "units": "file_units_assumed_mm",
            "point_count": len(points),
            "bounding_box": {"min": mins.tolist(), "max": maxs.tolist(), "size": (maxs-mins).tolist()},
            "feature_extraction": {"method": "Cartesian-point fallback", "topology_features": None, "status": "limited"},
            "provenance": {"source": "STEP", "method": "kernel failed; bounded Cartesian-point fallback", "warning": "Full B-rep topology and unit declaration were not inferred."},
        }
    result.setdefault("filename", name)
    result.setdefault("file_size_bytes", len(raw))
    result.setdefault("provenance", {})
    result["provenance"]["synthetic"] = False
    result["provenance"]["visualization"] = "kernel-derived tessellation"
    return result
