from __future__ import annotations

import base64
import math
import os
import re
import tempfile
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from .operation_engine import run_tool_operation

APP_VERSION = "0.3.5"
PHYSICS_VERSION = "fdm-shrinkage-3"
app = FastAPI(title="Fabrient Engineering Service", version=APP_VERSION)
MAX_UPLOAD_BYTES = 25_000_000

class EngineeringInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    material: str
    machine: str
    process: str = "FDM"
    nozzle_mm: float = Field(default=.4, gt=0)
    layer_height_mm: float = Field(default=.2, gt=0)
    shrinkage_mean: float = Field(default=.003, ge=0, le=.05)
    shrinkage_std: float = Field(default=.0015, ge=0, le=.02)
    tolerance_lower_mm: float = 0
    tolerance_upper_mm: float = 0

class CalibrationObservation(BaseModel):
    predicted_mm: float = Field(gt=0)
    measured_mm: float = Field(gt=0)
    context: dict[str, Any] = {}

def baseline(x: EngineeringInput):
    b = x.nominal_mm * (1 - x.shrinkage_mean)
    s = math.sqrt((x.nominal_mm * x.shrinkage_std) ** 2 + (0.02 * x.layer_height_mm) ** 2)
    return b, s

def fit(obs):
    r = np.array([o.measured_mm - o.predicted_mm for o in obs], dtype=float)
    mean = float(r.mean()); std = float(r.std(ddof=1)) if len(r) > 1 else 0.
    mae = float(np.abs(r).mean()); mape = float(np.mean(np.abs(r) / np.array([o.measured_mm for o in obs])) * 100)
    return mean, std, mae, mape

def cad_kernel_step(raw: bytes):
    """Inspect STEP with CadQuery/OCCT without fabricating topology."""
    try:
        import cadquery as cq
    except Exception as e:
        return {"available": False, "error": f"CAD kernel unavailable: {e}", "topology_verified": False}
    with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
        f.write(raw); path = f.name
    try:
        shape = cq.importers.importStep(path)
        solids = shape.solids().vals() if hasattr(shape, "solids") else []
        valid = all(s.isValid() for s in solids) if solids else False
        bb = shape.val().BoundingBox() if hasattr(shape, "val") else None
        size = [float(bb.xlen), float(bb.ylen), float(bb.zlen)] if bb else None
        return {"available": True, "shape_type": shape.val().ShapeType() if hasattr(shape, "val") else None, "solid_count": len(solids), "all_solids_valid": valid, "bbox_file_units": size, "topology_verified": bool(solids and valid), "source": "CadQuery/OCCT"}
    except Exception as e:
        return {"available": True, "error": str(e), "topology_verified": False}
    finally:
        try: os.unlink(path)
        except OSError: pass

def step_info(raw: bytes):
    text = raw.decode("utf-8", "ignore")
    pts=[]; pat=re.compile(r"CARTESIAN_POINT\s*\([^;]*?\(\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)\s*\)", re.I|re.S)
    for m in pat.finditer(text):
        try: pts.append(tuple(float(v) for v in m.groups()))
        except ValueError: pass
    fallback={"parser":"point-inspector","point_count":len(pts),"topology_verified":False}
    if pts:
        a=np.asarray(pts); fallback["point_bbox_file_units"]=(a.max(0)-a.min(0)).tolist()
    kernel=cad_kernel_step(raw); fallback["cad_kernel"]=kernel; fallback["topology_verified"]=bool(kernel.get("topology_verified",False))
    if kernel.get("bbox_file_units"): fallback["bbox_file_units"]=kernel["bbox_file_units"]; fallback["bbox_source"]="CadQuery/OCCT"
    elif fallback.get("point_bbox_file_units"): fallback["bbox_file_units"]=fallback["point_bbox_file_units"]; fallback["bbox_source"]="STEP Cartesian points (limited visualization only)"
    return fallback

def payload_file(filename, raw, extra=None):
    if len(raw)>MAX_UPLOAD_BYTES: raise HTTPException(413,"uploaded file exceeds 25 MB")
    inspection=step_info(raw); bbox=inspection.get("bbox_file_units"); topo=bool(inspection.get("topology_verified"))
    return {**(extra or {}),"status":"validated" if topo else ("limited" if bbox else "blocked"),"filename":filename,"file_size_bytes":len(raw),"step_inspection":inspection,"bounding_box":{"size":bbox,"units":"STEP file units; not guessed","exact":topo} if bbox else None,"provenance":{"geometry_source":inspection.get("bbox_source","unavailable"),"topology_verified":topo,"synthetic":False}}

def extract(p):
    p=dict(p or {}); enc=p.pop("file_base64",None)
    if enc:
        try: raw=base64.b64decode(enc,validate=True)
        except Exception as e: raise HTTPException(422,"invalid base64") from e
        return payload_file(str(p.pop("filename","upload.step")),raw,p)
    if p.get("file_path"):
        raise HTTPException(422,"file_path is not readable by the engineering service; send file_base64 or multipart upload")
    return p

def risk_level(score: float)->str:
    if score>=.8:return "critical"
    if score>=.6:return "high"
    if score>=.35:return "medium"
    return "low"

def compute_risk_map(findings,uncertainty_sigma_mm=0.,tolerance_mm=0.):
    ranked=[]
    for i,finding in enumerate(findings):
        try: score=max(0.,min(1.,float(finding.get("risk_score",finding.get("score",0)))))
        except (TypeError,ValueError): score=0.
        if tolerance_mm>0: score=min(1.,score+min(.25,max(0.,float(uncertainty_sigma_mm))/float(tolerance_mm)*.05))
        ranked.append({"id":str(finding.get("id",f"finding-{i+1}")),"category":str(finding.get("category","engineering")),"message":str(finding.get("message","No description supplied")),"risk_score":score,"level":risk_level(score),"source":str(finding.get("source","supplied engineering evidence")),"position":finding.get("position",[0,0,0])})
    ranked.sort(key=lambda x:(-x["risk_score"],x["id"]))
    return {"risk_map":ranked,"summary":{k:sum(x["level"]==k for x in ranked) for k in ("critical","high","medium","low")},"provenance":{"method":"deterministic finding ranking","uncertainty_sigma_mm":float(uncertainty_sigma_mm),"tolerance_mm":float(tolerance_mm),"physical_acceptance":"not evaluated by risk map"}}

@app.get("/health")
def health(): return {"ok":True,"version":APP_VERSION,"physics_version":PHYSICS_VERSION}
@app.get("/v1/health")
def v1health(): return health()
@app.post("/v1/predict")
def predict(x:EngineeringInput):
    b,s=baseline(x); return {"predicted_mm":b,"interval_low_mm":b-1.96*s,"interval_high_mm":b+1.96*s,"status":"uncalibrated","provenance":{"physics_version":PHYSICS_VERSION,"real_data":False}}
@app.post("/v1/calibrate")
def calibrate(obs:list[CalibrationObservation]):
    if len(obs)<10: raise HTTPException(422,"At least 10 real observations are required for validation")
    m,s,mae,mape=fit(obs); return {"status":"validated","n":len(obs),"residual_mean_mm":m,"residual_std_mm":s,"mae_mm":mae,"mape_percent":mape,"accuracy_target_met":mape<=1.,"source":"real_observations_only"}
@app.post("/v1/geometry/step")
async def geometry_step(file:UploadFile=File(...)):
    raw=await file.read()
    if not file.filename or not file.filename.lower().endswith((".step",".stp")): raise HTTPException(422,"Expected STEP/STP")
    if not raw: raise HTTPException(422,"Empty STEP file")
    return payload_file(file.filename,raw)
@app.post("/v1/geometry/step-json")
def geometry_step_json(payload:dict[str,Any]):
    filename=str(payload.get("filename","upload.step"))
    if not filename.lower().endswith((".step",".stp")): raise HTTPException(422,"Expected STEP/STP")
    return extract(payload)
@app.post("/v1/risk-map")
def risk_map(payload:dict[str,Any]):
    findings=payload.get("findings",[])
    if not isinstance(findings,list): raise HTTPException(422,"findings must be an array")
    return compute_risk_map(findings,float(payload.get("uncertainty_sigma_mm",0.)),float(payload.get("tolerance_mm",0.)))
@app.post("/v1/toolbox/{operation}")
def toolbox(operation:str,payload:dict[str,Any]|None=None):
    p=extract(payload or {})
    g=p.get("step_inspection") or {}
    topo=bool(g.get("topology_verified",False))
    if operation == "risk_map":
        return compute_risk_map(p.get("findings",[]),float(p.get("uncertainty_sigma_mm",0)),float(p.get("tolerance_mm",0)))
    return run_tool_operation(operation,p,topology_verified=topo)
@app.post("/v1/dfm/analyze")
def dfm(payload:dict[str,Any]): return toolbox("analyze_dfm",payload)
@app.post("/v1/dfm/self-fix")
def self_fix(payload:dict[str,Any]): return toolbox("auto_fix_dfm",payload)
@app.post("/v1/sim2real/calibrate-and-run")
def sim2real(payload:dict[str,Any]):
    obs=[CalibrationObservation(**x) for x in payload.get("real_observations",[])]
    if len(obs)<10:return {"status":"blocked","reason":"real observations required","required":10,"received":len(obs)}
    m,s,mae,mape=fit(obs); return {"status":"validated" if mape<=1 else "blocked","n":len(obs),"mae_mm":mae,"mape_percent":mape,"residual_std_mm":s,"accuracy_target_met":mape<=1,"source":"real_observations_only"}
@app.post("/v1/cv/measure")
async def cv_measure(image:UploadFile=File(...),reference_length_mm:float|None=None,reference_pixel_span:float|None=None):
    if not reference_length_mm or not reference_pixel_span or reference_length_mm<=0 or reference_pixel_span<=0: raise HTTPException(422,"Calibrated physical reference length and pixel span required")
    data=await image.read()
    if len(data)>MAX_UPLOAD_BYTES: raise HTTPException(413,"uploaded image exceeds 25 MB")
    import cv2
    arr=np.frombuffer(data,np.uint8); img=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
    if img is None: raise HTTPException(422,"invalid image")
    return {"status":"calibrated","mm_per_pixel":reference_length_mm/reference_pixel_span,"uncertainty":"requires repeatability/ground-truth validation","target_accuracy_percent":1.0}
@app.post("/v1/manufacturing/package")
def package(payload:dict[str,Any]):
    p=extract(payload); a=toolbox("analyze_dfm",p); return {"release_status":"HUMAN_RELEASE_REQUIRED","candidate":True,"contents":["geometry.step","dfm.json","inspection-plan.json","traceability.json","release-notes.txt"],"analysis":a,"physical_acceptance":"PENDING_REAL_BUILD"}
@app.post("/v1/manufacturing/build-guide")
def guide(payload:dict[str,Any]): return run_tool_operation("generate_physical_build_guide",payload)
@app.post("/v1/acceptance")
def acceptance(payload:dict[str,Any]): return run_tool_operation("acceptance_gate",payload)
@app.post("/v1/agents/fleet")
def fleet(payload:dict[str,Any]):
    operations=["inspect_part","analyze_dfm","run_bounded_engineering_review","fit_residual_model"]
    results=[run_tool_operation(op,payload,topology_verified=bool(payload.get("geometry_verified"))) for op in operations]
    return {"status":"completed_with_gates","agents":["geometry","dfm","physics","cv","sim2real","critic"],"results":results,"evidence_policy":"measured evidence only"}
