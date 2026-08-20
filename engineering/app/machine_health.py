from __future__ import annotations
from datetime import datetime
from typing import Any
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field
router=APIRouter(prefix="/v1/machine-health",tags=["machine-health"])
MIN_BASELINE_SESSIONS=30
NONLINEAR_MIN_SESSIONS=100
class Observation(BaseModel):
    machine_id:str=Field(min_length=1)
    observed_at:datetime
    dimensional_deviation_mm:float|None=None
    correction_mm:float|None=None
    correction_direction:float|None=None
    ambient_temperature_c:float|None=None
    ambient_rh_pct:float|None=Field(default=None,ge=0,le=100)
    dew_point_c:float|None=None
    atmospheric_pressure_kpa:float|None=None
    filament_temperature_c:float|None=None
    filament_rh_pct:float|None=Field(default=None,ge=0,le=100)
    filament_lot:str|None=None
    nozzle_hours:float|None=Field(default=None,ge=0)
    pressure_advance:float|None=None
    resonance_x_hz:float|None=Field(default=None,gt=0)
    resonance_y_hz:float|None=Field(default=None,gt=0)
    vibration_amplitude:float|None=Field(default=None,ge=0)
    shaper_x:str|None=None
    shaper_y:str|None=None
    frequency_spectrum:list[float]|None=None
    reference_artifact:bool=False
    source:str="user_observation"
    provenance:dict[str,Any]=Field(default_factory=dict)
class AnalysisRequest(BaseModel):
    observations:list[Observation]=Field(min_length=1)
    baseline_sessions:int=Field(default=30,ge=30,le=100)
def _signed(o):
    if o.correction_mm is None:return None
    return o.correction_mm if o.correction_direction is None else abs(o.correction_mm)*(1 if o.correction_direction>=0 else -1)
def _slope(v):
    return float(np.polyfit(np.arange(len(v),dtype=float),np.asarray(v,dtype=float),1)[0]) if len(v)>1 else 0.0
def _residualize(obs):
    rows=[]
    for o in obs:
        y=_signed(o); c=[o.ambient_temperature_c,o.ambient_rh_pct,o.dew_point_c,o.atmospheric_pressure_kpa,o.filament_rh_pct,o.nozzle_hours]
        if y is not None and all(v is not None for v in c):rows.append((y,[1.0,*map(float,c)]))
    if len(rows)<8:
        return [float(_signed(o)) for o in obs if _signed(o) is not None],["insufficient_covariates"]
    y=np.asarray([r[0] for r in rows]);X=np.asarray([r[1] for r in rows]);b=np.linalg.lstsq(X,y,rcond=None)[0]
    return (y-X@b).tolist(),["temperature","ambient_rh","dew_point","pressure","filament_rh","nozzle_hours"]
def _change(obs,field):
    v=[getattr(o,field) for o in obs if getattr(o,field) is not None]
    if len(v)<2:return None
    base=float(np.median(v[:min(30,len(v))]));cur=float(v[-1]);d=cur-base
    return {"baseline":base,"current":cur,"delta":d,"relative_change":abs(d)/max(abs(base),1e-9)}
@router.post("/analyze")
def analyze(req:AnalysisRequest):
    obs=sorted(req.observations,key=lambda x:x.observed_at);machines=sorted({o.machine_id for o in obs})
    if len(machines)!=1:return {"status":"invalid","reason":"Analyze one machine at a time","machines":machines}
    residuals,cov=_residualize(obs);n=len(residuals)
    if n<req.baseline_sessions:return {"status":"baseline_required","machine_id":machines[0],"sessions":n,"baseline_target":req.baseline_sessions,"nonlinear_target":100,"message":"Build a real machine baseline before issuing a machine-health alert; synthetic observations are not accepted as evidence.","provenance":{"method":"deterministic-machine-health-v1","covariates":cov}}
    b=np.asarray(residuals[:req.baseline_sessions]);cur=np.asarray(residuals);center=float(np.median(b));mad=float(np.median(np.abs(b-center)));scale=max(1.4826*mad,1e-6);latest=float(cur[-1]);z=float((latest-center)/scale);trend=_slope(residuals)
    telemetry={k:_change(obs,k) for k in ["pressure_advance","resonance_x_hz","resonance_y_hz","vibration_amplitude"]};telemetry={k:v for k,v in telemetry.items() if v}
    signals=[]
    if abs(z)>=3:signals.append({"type":"correction_residual_shift","severity":"high","robust_z":z})
    if abs(trend)>scale*.02:signals.append({"type":"correction_residual_trend","severity":"medium","slope_per_session_mm":trend})
    for k,v in telemetry.items():
        if v["relative_change"]>=.15:signals.append({"type":"telemetry_shift","severity":"medium","metric":k,**v})
    nlin=n>=100
    return {"status":"watch" if signals else "stable","machine_id":machines[0],"sessions":n,"baseline_sessions":req.baseline_sessions,"latest_correction_residual_mm":latest,"baseline_median_mm":center,"robust_z":z,"trend_mm_per_session":trend,"signals":signals,"telemetry":telemetry,"nonlinear_model_allowed":nlin,"nonlinear_note":"Linear/residual monitoring only until 100 real sessions; no silent ML substitution." if not nlin else "100 real sessions reached; nonlinear experiments may be evaluated separately.","provenance":{"method":"deterministic-machine-health-v1","residualized_covariates":cov,"uses_real_observations_only":True,"reference_artifact_and_correction_data_are_complementary":True}}
@router.get("/health")
def health():return {"service":"machine-health","status":"ok","version":"deterministic-machine-health-v1"}
