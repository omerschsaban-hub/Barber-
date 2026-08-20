from __future__ import annotations

import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.cad_kernel import extract_step

router = APIRouter(prefix="/v1/geometry", tags=["cad"])


@router.post("/step")
async def step_geometry(file: UploadFile = File(...)):
    name = (file.filename or "").lower()
    if not name.endswith((".step", ".stp")):
        raise HTTPException(415, "Only STEP/STP is accepted")
    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(422, "Empty STEP file")
    if len(raw) > 25_000_000:
        raise HTTPException(413, "Geometry exceeds 25 MB limit")
    with tempfile.TemporaryDirectory(prefix="fabrient-step-") as d:
        path = Path(d) / Path(file.filename or "model.step").name
        path.write_bytes(raw)
        result = extract_step(str(path))
    if result.get("status") == "error":
        raise HTTPException(422, result.get("reason", "STEP extraction failed"))
    result.setdefault("filename", file.filename)
    result.setdefault("file_size_bytes", len(raw))
    result.setdefault("provenance", {})
    result["provenance"]["synthetic"] = False
    result["provenance"]["visualization"] = "kernel-derived bounding box only"
    return result
