from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import numpy as np
from sklearn.linear_model import Ridge

app=FastAPI(title='Fabrient Engineering API',version='0.1.0')

class EngineeringInput(BaseModel):
    nominal_mm: float=Field(gt=0)
    material: str
    machine: str
    process_temperature_c: float=Field(gt=0)
    ambient_temperature_c: float=Field(default=23,gt=-50)
    nominal_shrinkage_pct: float=Field(default=0.5,ge=0,le=10)
    shrinkage_uncertainty_pct: float=Field(default=0.15,ge=0,le=5)
    tolerance_lower_mm: float=0
    tolerance_upper_mm: float=0

class Observation(BaseModel):
    predicted_mm: float
    measured_mm: float

class CalibrationRequest(BaseModel):
    observations: list[Observation]

@app.get('/health')
def health(): return {'ok':True,'service':'fabrient-engineering'}

def physics(x:EngineeringInput):
    shrink=x.nominal_shrinkage_pct/100
    predicted=x.nominal_mm*(1-shrink)
    sigma=max(x.nominal_mm*x.shrinkage_uncertainty_pct/100,0.001)
    return predicted,sigma

@app.post('/v1/predict')
def predict(x:EngineeringInput):
    predicted,sigma=physics(x)
    return {'prediction_mm':predicted,'interval_95_mm':[predicted-1.96*sigma,predicted+1.96*sigma], 'physics_uncertainty_mm':sigma,'status':'not_calibrated','provenance':{'source':'deterministic_physics','version':'physics-0.1'}}

@app.post('/v1/calibrate')
def calibrate(x:CalibrationRequest):
    if len(x.observations)<3:return {'status':'limited','reason':'At least 3 real observations are required; no synthetic data is used.'}
    X=np.array([[o.predicted_mm] for o in x.observations]); y=np.array([o.measured_mm-o.predicted_mm for o in x.observations])
    model=Ridge(alpha=1.0).fit(X,y)
    residuals=y-model.predict(X)
    sigma=float(max(np.std(residuals,ddof=1) if len(residuals)>1 else 0.001,0.001))
    return {'status':'limited' if len(x.observations)<8 else 'validated','model':'ridge-residual-v1','coefficient':float(model.coef_[0]),'intercept_mm':float(model.intercept_),'residual_sigma_mm':sigma,'n':len(x.observations)}

@app.post('/v1/cv/measure')
async def measure(file:UploadFile=File(...)):
    data=await file.read()
    try:
        import cv2
        arr=np.frombuffer(data,np.uint8); image=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
        if image is None: raise ValueError('unsupported image')
        edges=cv2.Canny(image,50,150)
        lines=cv2.HoughLinesP(edges,1,np.pi/180,threshold=80,minLineLength=max(30,image.shape[1]//5),maxLineGap=10)
        count=0 if lines is None else len(lines)
        return {'status':'limited','features_detected':count,'measurement_mm':None,'confidence':'unknown','reason':'A physical scale/reference feature is required before pixel measurements can become millimetres.'}
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/v1/next-experiment')
def next_experiment(machine_id:str='unknown'):
    return {'machine_id':machine_id,'experiment':{'type':'calibration_coupon','dimensions_mm':[20,20,10],'features':['20mm X','20mm Y','10mm Z'],'reason':'No measured residual history is available; establish a real baseline before optimizing experiments.','expected_information_gain':'high'}}
