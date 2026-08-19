from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Literal
import math, numpy as np
APP_VERSION='0.1.0'; PHYSICS_VERSION='fdm-shrinkage-1'
app=FastAPI(title='Fabrient Engineering Service',version=APP_VERSION)
class EngineeringInput(BaseModel):
    nominal_mm: float=Field(gt=0); material:str; machine:str; process:str='FDM'; nozzle_mm:float=Field(default=.4,gt=0); layer_height_mm:float=Field(default=.2,gt=0); bed_temp_c:float|None=None; nozzle_temp_c:float|None=None; infill_percent:float=Field(default=100,ge=0,le=100); shrinkage_mean:float=Field(default=.003,ge=0,le=.05); shrinkage_std:float=Field(default=.0015,ge=0,le=.02); tolerance_lower_mm:float=0; tolerance_upper_mm:float=0
class CalibrationObservation(BaseModel): predicted_mm:float=Field(gt=0); measured_mm:float=Field(gt=0); context:dict={}
def baseline(x): return x.nominal_mm*(1-x.shrinkage_mean), math.sqrt((x.nominal_mm*x.shrinkage_std)**2+(0.02*x.layer_height_mm)**2)
def fit(obs):
    if len(obs)<3:return 0.,None,'not_calibrated'
    r=np.array([o.measured_mm-o.predicted_mm for o in obs]); return float(r.mean()),float(r.std(ddof=1)),'validated' if len(obs)>=10 else 'limited'
@app.get('/health')
def health():return {'ok':True,'version':APP_VERSION}
@app.post('/physics/predict')
def predict(x:EngineeringInput):
    if x.tolerance_lower_mm>0 or x.tolerance_upper_mm<0: raise HTTPException(422,'Invalid tolerance convention')
    b,s=baseline(x); return {'baseline_mm':b,'residual_mm':0,'predicted_mm':b,'interval_low_mm':b-1.96*s,'interval_high_mm':b+1.96*s,'status':'not_calibrated','provenance':{'physics_version':PHYSICS_VERSION,'measured_data':False}}
@app.post('/calibration/fit')
def calibration(obs:list[CalibrationObservation]):
    if not obs:raise HTTPException(400,'Real observations required')
    m,s,status=fit(obs);return {'residual_mean_mm':m,'residual_std_mm':s,'status':status,'n':len(obs),'source':'real_observations_only'}
@app.post('/cv/measure')
async def cv_measure(image:UploadFile=File(...),reference_length_mm:float|None=None):
    if not reference_length_mm or reference_length_mm<=0:raise HTTPException(422,'Physical reference length required; pixels cannot become millimetres without scale.')
    import cv2
    data=await image.read(); arr=np.frombuffer(data,np.uint8); img=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
    if img is None:raise HTTPException(422,'Invalid image')
    edges=cv2.Canny(img,50,150); contours,_=cv2.findContours(edges,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); px=max((cv2.boundingRect(c)[2] for c in contours),default=0)
    if not px:raise HTTPException(422,'No measurable feature found')
    return {'pixels':int(px),'reference_length_mm':reference_length_mm,'measurement_mm':None,'status':'needs_reference_pixel_span','confidence':'limited'}
@app.post('/experiments/next')
def next_experiment(features:list[dict]):
    if not features:raise HTTPException(400,'No uncertainty-bearing features')
    t=max(features,key=lambda f:float(f.get('uncertainty_mm',0)));return {'selected_feature':t,'criterion':'maximum current uncertainty','requires_real_measurement':True}
