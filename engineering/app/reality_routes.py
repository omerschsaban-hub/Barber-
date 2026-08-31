from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from .reality_engine import Observation, active_experiment, autonomous_plan, compare, fit_residual_model, physics_predict, trust_envelope

router = APIRouter(prefix="/v1/sim2real", tags=["reality-loop"])

class RealityObservation(BaseModel):
    predicted_mm: float
    measured_mm: float
    layer_height_mm: float = 0.2
    print_speed_mm_s: float = 50.0
    nozzle_temp_c: float = 200.0
    ambient_temp_c: float = 23.0
    humidity_pct: float = 50.0
    axis: int = Field(default=0, ge=0, le=2)
    machine_id: str | None = None
    feature_id: str | None = None
    observation_id: str | None = None
    experiment_id: str | None = None

class RealityRequest(BaseModel):
    nominal_mm: float = 10.0
    predicted_mm: float | None = None
    observations: list[RealityObservation] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    target_mae_mm: float | None = Field(default=None, gt=0)
    scale: float = 1.0
    bias: float = 0.0


def _obs(x: RealityRequest) -> list[Observation]:
    out=[]
    for o in x.observations:
        out.append(Observation(
            predicted=o.predicted_mm, measured=o.measured_mm,
            features=(o.layer_height_mm,o.print_speed_mm_s,o.nozzle_temp_c,o.ambient_temp_c,o.humidity_pct,float(o.axis)),
            group=o.machine_id or o.feature_id or o.observation_id or "default",
            experiment_id=o.experiment_id or o.observation_id or o.feature_id or "",
        ))
    return out

@router.post("/run")
def run(x: RealityRequest):
    observations=_obs(x); base=physics_predict({"predicted": x.predicted_mm or x.nominal_mm, "scale": x.scale, "bias": x.bias}); fitted=fit_residual_model(observations); comparison=compare(observations); trust=trust_envelope(observations,fitted)
    return {"status":"real_calibrated" if fitted.get("status")=="validated" else ("real_informed" if len(observations)>=8 else "physics_only"),"physics":base,"prediction_mm":base["prediction"],"prediction_vs_reality":comparison,"calibration":{k:v for k,v in fitted.items() if k!="_model"},"trust_envelope":trust,"next_experiment":active_experiment(observations,x.candidates),"provenance":{"engine":"reality-loop","version":"reality-loop-1.0","real_data_only":True,"no_fabricated_measurements":True}}

@router.post("/compare")
def compare_route(x: RealityRequest):
    return {"comparison":compare(_obs(x)),"provenance":{"real_data_only":True}}

@router.post("/calibrate-and-run")
def calibrate_and_run(x: RealityRequest):
    observations=_obs(x); result=autonomous_plan(observations,x.candidates,x.target_mae_mm)
    return {**result,"release_claim":"validated only when held-out validation passes; this is not a physical safety or acceptance guarantee"}

@router.post("/next-experiment")
def next_experiment(x: RealityRequest):
    return active_experiment(_obs(x),x.candidates)

@router.post("/autonomous")
def autonomous(x: RealityRequest):
    return autonomous_plan(_obs(x),x.candidates,x.target_mae_mm)

@router.post("/trust-envelope")
def trust(x: RealityRequest):
    observations=_obs(x); fitted=fit_residual_model(observations); return trust_envelope(observations,fitted)
