from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Any
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ENGINE_VERSION = "reality-loop-1.0"
MIN_REAL = 8
MIN_HELD_OUT = 10
@dataclass(frozen=True)
class Observation:
    predicted: float
    measured: float
    features: tuple[float, ...] = ()
    group: str = "default"
    experiment_id: str = ""
def _mae(a,b): return float(np.mean(np.abs(a-b)))
def _rmse(a,b): return float(np.sqrt(np.mean(np.square(a-b))))
def _feature_matrix(obs):
    width=max((len(o.features) for o in obs),default=0)
    return np.asarray([[o.predicted,*list(o.features)[:width]] for o in obs],dtype=float)
def compare(observations):
    if not observations: return {"status":"needs_real_data","n":0}
    p=np.asarray([o.predicted for o in observations],float); m=np.asarray([o.measured for o in observations],float); r=m-p; i=int(np.argmax(np.abs(r)))
    return {"status":"available","n":len(observations),"mae":_mae(m,p),"rmse":_rmse(m,p),"mean_residual":float(np.mean(r)),"residual_sigma":float(np.std(r,ddof=1)) if len(r)>1 else 0.0,"worst":{"index":i,"experiment_id":observations[i].experiment_id,"predicted":float(p[i]),"measured":float(m[i]),"residual":float(r[i])},"divergence":{"index":i,"magnitude":float(abs(r[i])),"reason":"largest observed prediction residual; causal attribution remains a hypothesis until tested"}}
def fit_residual_model(observations):
    n=len(observations)
    if n<MIN_REAL: return {"status":"not_ready","n":n,"required":MIN_REAL,"model":None}
    X=_feature_matrix(observations); y=np.asarray([o.measured-o.predicted for o in observations],float); model=make_pipeline(StandardScaler(),Ridge(alpha=1.0)).fit(X,y); groups=np.asarray([o.group for o in observations]); unique=np.unique(groups); preds=np.empty(n,float)
    if len(unique)>=3:
        for g in unique:
            train=groups!=g
            if train.sum()<3: return {"status":"not_validated","n":n,"reason":"Insufficient independent training data.","model":None}
            c=make_pipeline(StandardScaler(),Ridge(alpha=1.0)).fit(X[train],y[train]); preds[groups==g]=c.predict(X[groups==g])
        validation="group_holdout"
    else:
        for i in range(n):
            train=np.arange(n)!=i; c=make_pipeline(StandardScaler(),Ridge(alpha=1.0)).fit(X[train],y[train]); preds[i]=c.predict(X[i:i+1])[0]
        validation="leave_one_out"
    mae=_mae(y,preds); q95=float(np.quantile(np.abs(y-preds),.95,method="higher")); training_mae=_mae(y,model.predict(X))
    return {"status":"validated" if n>=MIN_HELD_OUT else "limited","n":n,"groups":int(len(unique)),"model":"physics-plus-ridge-residual","version":ENGINE_VERSION,"validation":validation,"held_out_mae":mae,"held_out_q95_abs_error":q95,"training_mae":training_mae,"generalization_gap":max(0.0,mae-training_mae),"_model":model}
def physics_predict(state):
    predicted=float(state.get("predicted",state.get("nominal",0.0)))
    if predicted==0: raise ValueError("predicted or nominal must be non-zero")
    scale=float(state.get("scale",1.0)); bias=float(state.get("bias",0.0)); return {"prediction":predicted*scale+bias,"physics_model":"bounded-affine-baseline","parameters":{"scale":scale,"bias":bias}}
def active_experiment(observations,candidates=None):
    candidates=candidates or []
    if not candidates:
        if not observations: return {"status":"needs_real_data","reason":"A baseline physical observation is required before selecting a targeted experiment."}
        worst=max(observations,key=lambda o:abs(o.measured-o.predicted)); return {"status":"proposed","experiment":{"target":worst.experiment_id or "largest-residual-condition","reason":"repeat the largest-residual condition with an independent run","expected_information_gain":abs(worst.measured-worst.predicted)},"execution":"awaiting_external_executor"}
    scored=[]
    for c in candidates:
        s=np.asarray(c.get("sensitivity",[]),float); noise=max(float(c.get("noise",1.0)),1e-9); cost=max(float(c.get("cost",1.0)),1e-9); fisher=float(np.dot(s,s)/noise) if s.size else float(c.get("uncertainty",0.0)); scored.append((fisher/cost,c,fisher))
    score,candidate,fisher=max(scored,key=lambda x:x[0]); return {"status":"proposed","experiment":candidate,"expected_information_gain":fisher,"information_per_cost":score,"selection":"fisher_information_like_score","execution":"awaiting_external_executor"}
def trust_envelope(observations,fitted):
    if not observations: return {"status":"unknown","confidence":0.0,"bounds":{}}
    p=np.asarray([o.predicted for o in observations],float); m=np.asarray([o.measured for o in observations],float); r=np.abs(m-p); q95=float(np.quantile(r,.95)) if len(r)>1 else float(r[0]); confidence=0.0 if fitted.get("status")=="not_ready" else max(0.0,min(.99,1.0-q95/max(float(np.mean(np.abs(m))),1e-9)))
    return {"status":"validated" if fitted.get("status")=="validated" else "limited","confidence":confidence,"bounds":{"prediction_min":float(np.min(p)),"prediction_max":float(np.max(p)),"observed_min":float(np.min(m)),"observed_max":float(np.max(m)),"held_out_abs_error_q95":float(fitted.get("held_out_q95_abs_error",q95))},"warning":"Observed validation envelope only; not a universal safety guarantee."}
def autonomous_plan(observations,candidates=None,target_mae=None):
    comparison=compare(observations); fitted=fit_residual_model(observations); trust=trust_envelope(observations,fitted); current_mae=comparison.get("mae"); done=bool(fitted.get("status")=="validated" and (target_mae is None or (current_mae is not None and current_mae<=target_mae))); next_step={"action":"validate_holdout_and_freeze","reason":"Target error reached with independent validation."} if done else active_experiment(observations,candidates); fingerprint=hashlib.sha256(repr([(o.predicted,o.measured,o.features,o.group) for o in observations]).encode()).hexdigest()[:16]
    return {"status":"validated" if done else "loop_open","version":ENGINE_VERSION,"comparison":comparison,"calibration":{k:v for k,v in fitted.items() if k!="_model"},"trust_envelope":trust,"next_action":next_step,"input_fingerprint":fingerprint,"manual_work":"none inside Fabrient; physical execution requires a connected external test executor when no robot/test API is available","evidence_policy":"real observations only; no fabricated measurements, confidence, or validation"}
