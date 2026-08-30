from __future__ import annotations

import hashlib
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .postgres_artifacts import put_bytes
from .owned_auth import _bearer, user_from_token

router = APIRouter(prefix="/v1/cad", tags=["cad-generation"])
MAX_ARTIFACT_BYTES = 25_000_000

class CadGenerationRequest(BaseModel):
    intent: str = Field(min_length=3, max_length=8000)
    dimensions_mm: dict[str, float] | None = None
    component_context: dict[str, Any] = {}
    require_step: bool = True
    validation_level: str = "release"

def _identity(request: Request) -> dict:
    identity = user_from_token(_bearer(request, request.headers.get("authorization")))
    if not identity: raise HTTPException(401, "A valid Fabrient session is required.")
    return identity

def _validate_step(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size < 128: raise RuntimeError("STEP export was not produced or is empty")
    data = path.read_bytes(); head = data[:4096].decode("latin-1", errors="ignore")
    if "ISO-10303-21" not in head or "END-ISO-10303-21" not in data[-4096:].decode("latin-1", errors="ignore"): raise RuntimeError("Generated file does not pass STEP exchange-format validation")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def _persist_step(owner_id: str, data: bytes, sha256: str) -> dict[str, Any]:
    artifact = put_bytes(artifact_id=str(uuid.uuid4()), owner_id=owner_id, project_id=None,
                         filename="fabrient_generated.step", content_type="application/step",
                         data=data, max_bytes=MAX_ARTIFACT_BYTES)
    return {"mode":"postgres", "durable":True, "artifact_id":artifact.id,
            "size_bytes":artifact.size_bytes, "sha256":sha256}

@router.post("/generate")
def generate_cad(x: CadGenerationRequest, request: Request):
    identity = _identity(request)
    if not x.require_step: raise HTTPException(422, "Fabrient CAD generation requires a STEP deliverable.")
    try: import cadquery as cq
    except Exception as exc: raise HTTPException(503, "CAD kernel unavailable; no geometry was accepted.") from exc
    dims=x.dimensions_mm or {}; width=float(dims.get("width",100)); depth=float(dims.get("depth",60)); height=float(dims.get("height",25)); wall=float(dims.get("wall",2))
    if min(width,depth,height,wall)<=0 or 2*wall>=min(width,depth): raise HTTPException(422,"Invalid enclosure dimensions/wall thickness.")
    outer=cq.Workplane("XY").box(width,depth,height); inner=cq.Workplane("XY").box(width-2*wall,depth-2*wall,height-wall).translate((0,0,wall/2)); result=outer.cut(inner)
    with tempfile.TemporaryDirectory() as td:
        step=Path(td)/"fabrient_generated.step"; result.export(str(step),"STEP",unit="MM",outputUnit="MM"); validation=_validate_step(step); raw=step.read_bytes()
        storage=_persist_step(identity["id"],raw,validation["sha256"])
    return {"status":"generated","format":"STEP","step_required":True,"geometry_authority":"deterministic_cad_kernel","intent":x.intent,"parameters_mm":{"width":width,"depth":depth,"height":height,"wall":wall},"validation":{"format":"passed",**validation,"topology":"kernel_validation_required_before_release"},"provenance":{"synthetic":False,"llm_role":"intent_and_plan_only","cad_kernel":"CadQuery/OCCT"},"release_gate":"blocked_until_geometry_topology_dfm_and_step_roundtrip_checks_pass","storage":storage}
