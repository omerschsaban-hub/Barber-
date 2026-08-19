from __future__ import annotations
import math
from dataclasses import dataclass
from statistics import mean

@dataclass(frozen=True)
class ValidationResult:
    n:int
    mae:float
    rmse:float
    sigma:float
    calibrated:bool
    model_version:str

def fit_residual_linear(x:list[list[float]], y:list[float]):
    """Small-data ridge regression implemented without opaque deep learning."""
    if len(x)<5 or len(x)!=len(y): raise ValueError('at least 5 observations required')
    p=len(x[0]); lam=1e-3
    # Gaussian elimination on normal equations.
    A=[[0.0]*(p+1) for _ in range(p)]
    for row,target in zip(x,y):
        for i in range(p):
            for j in range(p): A[i][j]+=row[i]*row[j]
            A[i][p]+=row[i]*target
    for i in range(p): A[i][i]+=lam
    for i in range(p):
        k=max(range(i,p),key=lambda z:abs(A[z][i])); A[i],A[k]=A[k],A[i]
        if abs(A[i][i])<1e-12: raise ValueError('singular feature matrix')
        for k in range(i+1,p):
            q=A[k][i]/A[i][i]
            for j in range(i,p+1): A[k][j]-=q*A[i][j]
    w=[0.0]*p
    for i in range(p-1,-1,-1): w[i]=(A[i][p]-sum(A[i][j]*w[j] for j in range(i+1,p)))/A[i][i]
    return w

def predict(w:list[float], row:list[float])->float:return sum(a*b for a,b in zip(w,row))

def holdout_validate(x:list[list[float]],y:list[float])->ValidationResult:
    if len(x)<10: return ValidationResult(len(x),float('nan'),float('nan'),float('nan'),False,'residual-linear-v1')
    cut=max(5,int(len(x)*0.8)); w=fit_residual_linear(x[:cut],y[:cut]); errs=[predict(w,r)-t for r,t in zip(x[cut:],y[cut:])]
    mae=mean(abs(e) for e in errs); rmse=math.sqrt(mean(e*e for e in errs)); sigma=math.sqrt(mean((e-mean(errs))**2 for e in errs))
    # 95% empirical coverage cannot be claimed from fewer than 10 holdout points.
    return ValidationResult(len(x),mae,rmse,sigma,len(errs)>=10,'residual-linear-v1')
