from __future__ import annotations
import base64, io, math, os, re, tempfile
from datetime import datetime, timezone
from typing import Any
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

APP_VERSION='0.3.0'; PHYSICS_VERSION='fdm-shrinkage-3'; app=FastAPI(title='Fabrient Engineering Service',version=APP_VERSION)
class EngineeringInput(BaseModel):
 nominal_mm: float=Field(gt=0); material:str; machine:str; process:str='FDM'; nozzle_mm:float=Field(default=.4,gt=0); layer_height_mm:float=Field(default=.2,gt=0); shrinkage_mean:float=Field(default=.003,ge=0,le=.05); shrinkage_std:float=Field(default=.0015,ge=0,le=.02); tolerance_lower_mm:float=0; tolerance_upper_mm:float=0
class CalibrationObservation(BaseModel): predicted_mm:float=Field(gt=0); measured_mm:float=Field(gt=0); context:dict[str,Any]={}

def baseline(x):
 b=x.nominal_mm*(1-x.shrinkage_mean); s=math.sqrt((x.nominal_mm*x.shrinkage_std)**2+(0.02*x.layer_height_mm)**2); return b,s

def fit(obs):
 r=np.array([o.measured_mm-o.predicted_mm for o in obs],dtype=float); mean=float(r.mean()); std=float(r.std(ddof=1)) if len(r)>1 else 0.; mae=float(np.abs(r).mean()); mape=float(np.mean(np.abs(r)/np.array([o.measured_mm for o in obs]))*100); return mean,std,mae,mape

def cad_kernel_step(raw:bytes):
 try:
  import cadquery as cq
 except Exception as e: return {'available':False,'error':f'CAD kernel unavailable: {e}'}
 with tempfile.NamedTemporaryFile(suffix='.step',delete=False) as f: f.write(raw); path=f.name
 try:
  shape=cq.importers.importStep(path)
  solids=shape.solids().vals() if hasattr(shape,'solids') else []
  valid=all(s.isValid() for s in solids) if solids else False
  bb=shape.val().BoundingBox() if hasattr(shape,'val') else None
  return {'available':True,'shape_type':shape.val().ShapeType() if hasattr(shape,'val') else None,'solid_count':len(solids),'all_solids_valid':valid,'bbox_mm':[bb.xlen,bb.ylen,bb.zlen] if bb else None,'topology_verified':bool(solids and valid)}
 except Exception as e: return {'available':True,'error':str(e),'topology_verified':False}
 finally:
  try: os.unlink(path)
  except OSError: pass

def step_info(raw):
 text=raw.decode('utf-8','ignore'); pts=[]; pat=re.compile(r'CARTESIAN_POINT\s*\([^;]*?\(\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)\s*\)',re.I|re.S)
 for m in pat.finditer(text):
  try: pts.append(tuple(float(v) for v in m.groups()))
  except ValueError: pass
 fallback={'parser':'point-inspector','point_count':len(pts),'topology_verified':False}
 if pts:
  a=np.asarray(pts); fallback['bbox_mm']=(a.max(0)-a.min(0)).tolist()
 kernel=cad_kernel_step(raw); fallback['cad_kernel']=kernel; fallback['topology_verified']=kernel.get('topology_verified',False)
 return fallback

def payload_file(filename,raw,extra=None): return {**(extra or {}),'filename':filename,'file_size_bytes':len(raw),'step_inspection':step_info(raw)}
def extract(p):
 p=dict(p or {}); enc=p.pop('file_base64',None)
 if enc:
  try: raw=base64.b64decode(enc,validate=True)
  except Exception as e: raise HTTPException(422,'invalid base64') from e
  return payload_file(str(p.pop('filename','upload.step')),raw,p)
 return p

@app.get('/health')
def health(): return {'ok':True,'version':APP_VERSION,'physics_version':PHYSICS_VERSION}
@app.get('/v1/health')
def v1health(): return health()
@app.post('/v1/predict')
def predict(x:EngineeringInput):
 b,s=baseline(x); return {'predicted_mm':b,'interval_low_mm':b-1.96*s,'interval_high_mm':b+1.96*s,'status':'uncalibrated','provenance':{'physics_version':PHYSICS_VERSION,'real_data':False}}
@app.post('/v1/calibrate')
def calibrate(obs:list[CalibrationObservation]):
 if len(obs)<10: raise HTTPException(422,'At least 10 real observations are required for validation')
 m,s,mae,mape=fit(obs); return {'status':'validated','n':len(obs),'residual_mean_mm':m,'residual_std_mm':s,'mae_mm':mae,'mape_percent':mape,'accuracy_target_met':mape<=1.0,'source':'real_observations_only'}
@app.post('/v1/geometry/step')
async def geometry_step(file:UploadFile=File(...)):
 raw=await file.read();
 if not file.filename or not file.filename.lower().endswith(('.step','.stp')): raise HTTPException(422,'Expected STEP/STP')
 return payload_file(file.filename,raw)
@app.post('/v1/toolbox/{operation}')
def toolbox(operation:str,payload:dict[str,Any]|None=None):
 p=extract(payload or {}); g=p.get('step_inspection') or {}; topo=g.get('topology_verified',False)
 if operation in {'inspect_part','analyze_geometry','extract_features'}: return {'operation':operation,'geometry':g,'status':'pass' if topo else 'blocked'}
 if operation in {'analyze_dfm','find_manufacturing_risks','score_manufacturability','risk_map'}: return {'operation':operation,'risks':[] if topo else [{'code':'TOPOLOGY_UNVERIFIED','severity':'high'}],'status':'pass' if topo else 'blocked'}
 if operation=='auto_fix_dfm': return {'operation':operation,'status':'blocked','reason':'No arbitrary geometry rewrite without a detected, bounded fix and post-fix kernel verification'}
 if operation=='verify_fixes': return {'operation':operation,'status':'pass' if topo else 'blocked','topology_verified':topo}
 if operation=='build_inspection_plan': return {'inspection_plan':['critical dimensions','fit/clearance','surface/defects','material/process traceability']}
 if operation=='release_manufacturing_package': return {'released':False,'status':'human_release_required'}
 return {'operation':operation,'status':'unsupported_operation'}
@app.post('/v1/dfm/analyze')
def dfm(payload:dict[str,Any]): return toolbox('analyze_dfm',payload)
@app.post('/v1/dfm/self-fix')
def self_fix(payload:dict[str,Any]): return toolbox('auto_fix_dfm',payload)
@app.post('/v1/sim2real/calibrate-and-run')
def sim2real(payload:dict[str,Any]):
 obs=[CalibrationObservation(**x) for x in payload.get('real_observations',[])]
 if len(obs)<10: return {'status':'blocked','reason':'real observations required','required':10,'received':len(obs)}
 m,s,mae,mape=fit(obs); return {'status':'validated' if mape<=1 else 'blocked','n':len(obs),'mae_mm':mae,'mape_percent':mape,'residual_std_mm':s,'accuracy_target_met':mape<=1,'source':'real_observations_only'}
@app.post('/v1/cv/measure')
async def cv_measure(image:UploadFile=File(...),reference_length_mm:float|None=None,reference_pixel_span:float|None=None):
 if not reference_length_mm or not reference_pixel_span or reference_length_mm<=0 or reference_pixel_span<=0: raise HTTPException(422,'Calibrated physical reference length and pixel span required')
 data=await image.read(); import cv2; arr=np.frombuffer(data,np.uint8); img=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
 if img is None: raise HTTPException(422,'invalid image')
 return {'status':'calibrated','mm_per_pixel':reference_length_mm/reference_pixel_span,'uncertainty':'requires repeatability/ground-truth validation','target_accuracy_percent':1.0}
@app.post('/v1/manufacturing/package')
def package(payload:dict[str,Any]):
 p=extract(payload); a=toolbox('analyze_dfm',p); return {'release_status':'HUMAN_RELEASE_REQUIRED','candidate':True,'contents':['geometry.step','dfm.json','inspection-plan.json','traceability.json','release-notes.txt'],'analysis':a,'physical_acceptance':'PENDING_REAL_BUILD'}
@app.post('/v1/manufacturing/build-guide')
def guide(payload:dict[str,Any]): return {'title':'Fabrient Physical Build & Acceptance Guide','steps':['lock revision and provenance','manufacture controlled sample','measure calibrated critical dimensions','perform physical fit test','capture CV images with scale reference','record measurements','run held-out sim-to-real validation','review inspection report','human release gate'],'release':'not_authorized_until_physical_evidence'}
@app.post('/v1/acceptance')
def acceptance(payload:dict[str,Any]): return {'accepted':False,'status':'HUMAN_PHYSICAL_ACCEPTANCE_REQUIRED'}
@app.post('/v1/agents/fleet')
def fleet(payload:dict[str,Any]): return {'status':'completed_with_gates','agents':['geometry','dfm','physics','cv','sim2real','critic'],'evidence_policy':'measured evidence only'}
