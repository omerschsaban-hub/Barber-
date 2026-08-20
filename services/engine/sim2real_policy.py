from __future__ import annotations
from dataclasses import dataclass
import numpy as np

TARGET_MAPE_PERCENT = 1.0
MAX_CORRECTION_FACTOR = 0.05

@dataclass
class Fit:
    bias: float
    scale: float
    mae: float
    mape: float

def fit(predicted, measured) -> Fit:
    p=np.asarray(predicted,dtype=float); y=np.asarray(measured,dtype=float)
    if len(p)<10 or len(p)!=len(y): raise ValueError('at least 10 paired real observations required')
    A=np.column_stack([p,np.ones(len(p))])
    scale,bias=np.linalg.lstsq(A,y,rcond=None)[0]
    scale=float(np.clip(scale,1-MAX_CORRECTION_FACTOR,1+MAX_CORRECTION_FACTOR)); bias=float(bias)
    corrected=p*scale+bias; err=corrected-y
    mae=float(np.mean(np.abs(err)))
    mape=float(np.mean(np.abs(err)/np.maximum(np.abs(y),1e-9))*100)
    return Fit(bias,scale,mae,mape)

def auto_fix(predicted, measured, max_rounds=5):
    p=np.asarray(predicted,dtype=float); y=np.asarray(measured,dtype=float); history=[]
    for i in range(max_rounds):
        f=fit(p,y); history.append({'round':i+1,'scale':f.scale,'bias_mm':f.bias,'mae_mm':f.mae,'mape_percent':f.mape})
        if f.mape<=TARGET_MAPE_PERCENT: return f,history,True
        p=p*f.scale+f.bias
    f=fit(p,y); return f,history,f.mape<=TARGET_MAPE_PERCENT
