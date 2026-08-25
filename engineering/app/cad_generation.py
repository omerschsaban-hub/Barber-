from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/cad", tags=["cad-generation"])

class CadGenerationRequest(BaseModel):
    intent: str = Field(min_length=3, max_length=8000)
    dimensions_mm: dict[str, float] | None = None
    component_context: dict[str, Any] = {}
    require_step: bool = True
    validation_level: str = "release"


def _validate_step(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size < 128:
        raise RuntimeError("STEP export was not produced or is empty")
    data = path.read_bytes()
    head = data[:4096].decode("latin-1", errors="ignore")
    # STEP files are ISO-10303-21 exchange files. This is a format sanity check,
    # not a substitute for geometric/topological validation.
    if "ISO-10303-21" not in head or "END-ISO-10303-21" not in data[-4096:].decode("latin-1", errors="ignore"):
        raise RuntimeError("Generated file does not pass STEP exchange-format validation")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


@router.post("/generate")
def generate_cad(x: CadGenerationRequest):
    if not x.require_step:
        raise HTTPException(422, "Fabrient CAD generation requires a STEP deliverable.")

    # The LLM is an intent/planning layer; it must never directly author unchecked
    # geometry. The deterministic CAD kernel is the geometry authority.
    try:
        import cadquery as cq
    except Exception as exc:
        raise HTTPException(503, "CAD kernel unavailable; no geometry was accepted.") from exc

    dims = x.dimensions_mm or {}
    width = float(dims.get("width", 100))
    depth = float(dims.get("depth", 60))
    height = float(dims.get("height", 25))
    wall = float(dims.get("wall", 2))
    if min(width, depth, height, wall) <= 0 or 2 * wall >= min(width, depth):
        raise HTTPException(422, "Invalid enclosure dimensions/wall thickness.")

    # Deterministic baseline solid. Production intent-to-parameter mapping should
    # feed this kernel with an explicit, provenance-bearing parameter schema.
    outer = cq.Workplane("XY").box(width, depth, height)
    inner = cq.Workplane("XY").box(width - 2 * wall, depth - 2 * wall, height - wall).translate((0, 0, wall / 2))
    result = outer.cut(inner)

    with tempfile.TemporaryDirectory() as td:
        step = Path(td) / "fabrient_generated.step"
        result.export(str(step), "STEP", unit="MM", outputUnit="MM")
        validation = _validate_step(step)
        # Do not return a path that disappears after the request. The deployment
        # layer should replace this with object storage and a signed download URL.
        return {
            "status": "generated",
            "format": "STEP",
            "step_required": True,
            "geometry_authority": "deterministic_cad_kernel",
            "intent": x.intent,
            "parameters_mm": {"width": width, "depth": depth, "height": height, "wall": wall},
            "validation": {"format": "passed", **validation, "topology": "kernel_validation_required_before_release"},
            "provenance": {"synthetic": False, "llm_role": "intent_and_plan_only", "cad_kernel": "CadQuery/OCCT"},
            "release_gate": "blocked_until_geometry_topology_dfm_and_step_roundtrip_checks_pass",
        }
