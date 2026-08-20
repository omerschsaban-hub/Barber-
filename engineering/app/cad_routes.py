from __future__ import annotations

import base64
import binascii
import tempfile
from pathlib import Path

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
        if not isinstance(encoded, str) or not encoded:
            raise HTTPException(422, "JSON STEP request must contain file_base64")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(422, "file_base64 is not valid base64") from exc
    else:
        raise HTTPException(415, "STEP endpoint accepts multipart/form-data or application/json with file_base64")

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
        raise HTTPException(422, result.get("reason", "STEP extraction failed"))
    result.setdefault("filename", name)
    result.setdefault("file_size_bytes", len(raw))
    result.setdefault("provenance", {})
    result["provenance"]["synthetic"] = False
    result["provenance"]["visualization"] = "kernel-derived tessellation"
    return result
