from __future__ import annotations

import csv, io, math, re, statistics, hashlib
from datetime import datetime, timezone
from typing import Any, Literal

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_absolute_error

APP_VERSION = "1.0.0"
PHYSICS_VERSION = "fdm-linear-shrinkage-1.0"
ALGORITHM_VERSION = "deterministic-sim2real-1.0"

app = FastAPI(title="Fabrient Engineering API", version=APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

class EngineeringInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    material: str = Field(min_length=1)
    machine: str = Field(min_length=1)
    process_temperature_c: float = Field(gt=0, lt=400)
    ambient_temperature_c: float = Field(default=23, gt=-50, lt=100)
    nominal_shrinkage_pct: float = Field(default=0.5, ge=0, le=10)
    shrinkage_uncertainty_pct: float = Field(default=0.15, ge=0, le=5)
    tolerance_lower_mm: float = 0
    tolerance_upper_mm: float = 0
    feature_axis: Literal["x", "y", "z"] = "x"

class Observation(BaseModel):
    predicted_mm: float
    measured_mm: float
    machine_id: str | None = None
    feature_id: str | None = None
    context: dict[str, Any] = {}

class CalibrationRequest(BaseModel):
    observations: list[Observation]
    min_validation_points: int = Field(default=3, ge=2, le=20)

class ReverificationInput(BaseModel):
    tolerance_band_mm: float = Field(gt=0)
    uses_per_week: float = Field(ge=0)
    environment_severity: float = Field(ge=0, le=1)
    observed_drift_mm_per_day: float = Field(ge=0)
    consequence_severity: float = Field(ge=0, le=1)
    service_wear_mm_per_day: float = Field(default=0, ge=0)
    measurement_uncertainty_mm: float = Field(default=0, ge=0)

class SimulationInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    shrinkage_pct: float = Field(ge=0, le=10)
    shrinkage_sigma_pct: float = Field(ge=0, le=5)
    temperature_c: float = Field(gt=0, lt=400)
    temperature_sigma_c: float = Field(ge=0, le=50)
    n: int = Field(default=1000, ge=100, le=10000)
    seed: int = 42

class ExperimentInput(BaseModel):
    features: list[dict[str, Any]]
    current_uncertainty: dict[str, float] = {}
    budget: float = Field(default=1, ge=0)

class AcceptanceInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    lower_tol_mm: float
    upper_tol_mm: float
    observed_sigma_mm: float = Field(ge=0)
    measurement_sigma_mm: float = Field(ge=0)
    n_observations: int = Field(ge=0)

class UncertaintyInput(BaseModel):
    physics_sigma_mm: float = Field(default=0.0, ge=0)
    measurement_sigma_mm: float = Field(default=0.0, ge=0)
    model_sigma_mm: float = Field(default=0.0, ge=0)
    n_observations: int = Field(default=0, ge=0)

class AgentRequest(BaseModel):
    project_id: str
    objective: str
    max_iterations: int = Field(default=5, ge=1, le=20)


def physics(x: EngineeringInput) -> tuple[float, float]:
    shrink = x.nominal_shrinkage_pct / 100.0
    predicted = x.nominal_mm * (1 - shrink)
    sigma = max(x.nominal_mm * x.shrinkage_uncertainty_pct / 100.0, 1e-6)
    return predicted, sigma


def interval(mu: float, sigma: float) -> list[float]:
    return [mu - 1.96 * sigma, mu + 1.96 * sigma]


def status_for(n: int, validation_mae: float | None, tolerance: float | None) -> str:
    if n < 3: return "not_calibrated"
    if validation_mae is None or n < 6: return "limited"
    if tolerance is not None and validation_mae * 2 > tolerance: return "limited"
    return "validated"

@app.get("/health")
def health():
    return {"ok": True, "service": "fabrient-engineering", "version": APP_VERSION, "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/v1/predict")
def predict(x: EngineeringInput):
    if x.tolerance_lower_mm > 0 or x.tolerance_upper_mm < 0:
        raise HTTPException(422, "Tolerance bounds must be expressed as signed deviations from nominal.")
    mu, sigma = physics(x)
    lo, hi = interval(mu, sigma)
    return {"prediction_mm": mu, "interval_95_mm": [lo, hi], "physics_uncertainty_mm": sigma,
            "status": "not_calibrated", "provenance": {"source": "deterministic_physics", "physics_version": PHYSICS_VERSION, "algorithm_version": ALGORITHM_VERSION,
            "assumptions": {"temperature_used_as_context_only": True, "no_literature_value_substituted": True}}}

@app.post("/v1/simulate")
def simulate(x: SimulationInput):
    rng = np.random.default_rng(x.seed)
    shrink = rng.normal(x.shrinkage_pct, x.shrinkage_sigma_pct, x.n)
    temp = rng.normal(x.temperature_c, x.temperature_sigma_c, x.n)
    dims = x.nominal_mm * (1 - shrink / 100.0)
    return {"n": x.n, "seed": x.seed, "prediction_mm": float(np.mean(dims)),
            "interval_95_mm": [float(np.quantile(dims, .025)), float(np.quantile(dims, .975))],
            "domain_randomization": {"parameters": ["shrinkage_pct", "temperature_c"], "temperature_not_coupled_without_measured_coefficient": True},
            "samples_summary": {"sigma_mm": float(np.std(dims, ddof=1)), "min_mm": float(np.min(dims)), "max_mm": float(np.max(dims))},
            "provenance": {"source": "simulation", "version": "domain-randomization-1.0", "seed": x.seed}}

@app.post("/v1/calibrate")
def calibrate(x: CalibrationRequest):
    if len(x.observations) < 3:
        return {"status": "not_calibrated", "reason": "At least 3 real observations are required; no synthetic data is accepted."}
    pred = np.array([o.predicted_mm for o in x.observations], dtype=float)
    residual = np.array([o.measured_mm - o.predicted_mm for o in x.observations], dtype=float)
    X = pred.reshape(-1, 1)
    model = HuberRegressor(epsilon=1.35, alpha=0.01).fit(X, residual)
    if len(x.observations) >= 4:
        cv_pred = cross_val_predict(HuberRegressor(epsilon=1.35, alpha=0.01), X, residual, cv=LeaveOneOut())
        mae = float(mean_absolute_error(residual, cv_pred))
    else:
        mae = None
    fitted = model.predict(X)
    sigma = float(max(np.std(residual - fitted, ddof=1) if len(residual) > 1 else 0.0, 1e-6))
    tolerance = None
    status = status_for(len(x.observations), mae, tolerance)
    return {"status": status, "model": "huber-residual-v1", "coefficient": float(model.coef_[0]), "intercept_mm": float(model.intercept_),
            "residual_sigma_mm": sigma, "held_out_mae_mm": mae, "n": len(x.observations),
            "provenance": {"training_source": "real_observations_only", "validation": "leave_one_out", "model_version": "huber-residual-v1"}}

@app.post("/v1/uncertainty")
def uncertainty(x: UncertaintyInput):
    total = math.sqrt(x.physics_sigma_mm**2 + x.measurement_sigma_mm**2 + x.model_sigma_mm**2)
    return {"sigma_mm": total, "interval_multiplier": 1.96, "interval_95_mm": [-1.96*total, 1.96*total], "state": "not_calibrated" if x.n_observations < 3 else "limited", "components": {"physics": x.physics_sigma_mm, "measurement": x.measurement_sigma_mm, "model": x.model_sigma_mm}}

@app.post("/v1/acceptance")
def acceptance(x: AcceptanceInput):
    if x.n_observations < 3:
        return {"status": "refused", "reason": "Insufficient real observations to support an acceptance claim."}
    band = x.upper_tol_mm - x.lower_tol_mm
    if band <= 0: raise HTTPException(422, "Upper tolerance must exceed lower tolerance.")
    combined = math.sqrt(x.observed_sigma_mm**2 + x.measurement_sigma_mm**2)
    if 2 * 1.96 * combined > band:
        return {"status": "refused", "reason": "Observed variation plus measurement uncertainty consumes too much of the tolerance band.", "supported_tolerance_band_mm": 3.92*combined, "observed_sigma_mm": combined}
    return {"status": "supported", "tolerance_consumed_fraction": (3.92*combined)/band, "combined_sigma_mm": combined}

@app.post("/v1/reverification")
def reverification(x: ReverificationInput):
    if x.observed_drift_mm_per_day <= 0 and x.service_wear_mm_per_day <= 0:
        return {"status": "insufficient_data", "interval_days": None, "reason": "No observed drift/wear rate exists; establish real history before recommending an interval."}
    rate = max(x.observed_drift_mm_per_day, 1e-9)
    allowable = max(x.tolerance_band_mm/2 - x.measurement_uncertainty_mm, 0)
    if allowable <= 0:
        return {"status": "refused", "interval_days": None, "reason": "Measurement uncertainty leaves no defensible verification margin."}
    base = allowable / rate
    usage_factor = 1 / (1 + x.uses_per_week/50)
    env_factor = 1 - 0.6*x.environment_severity
    consequence_factor = 1 - 0.7*x.consequence_severity
    days = max(1, math.floor(base * usage_factor * env_factor * consequence_factor))
    return {"status": "supported", "interval_days": days, "inputs": x.model_dump(), "rationale": "Interval is bounded by half the tolerance margin, observed production drift, measurement uncertainty, use frequency, environment, and consequence severity. It is not a calibration standard."}

@app.post("/v1/next-experiment")
def next_experiment(x: ExperimentInput):
    if not x.features:
        return {"status": "insufficient_data", "reason": "No measured features available to select an information-gaining experiment."}
    ranked = sorted(x.features, key=lambda f: float(f.get("uncertainty_mm", 0)), reverse=True)
    target = ranked[0]
    return {"status": "proposed", "experiment": {"type": "targeted_calibration", "target": target,
        "reason": "Select the real feature with the largest measured uncertainty; do not optimize from synthetic observations.",
        "expected_information_gain": float(target.get("uncertainty_mm", 0))}, "guardrail": "human approval required before physical execution"}


def normalize_header(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")

FIELD_ALIASES = {
    "serial": {"serial", "serial_number", "gauge_serial", "fixture_serial", "id"},
    "machine": {"machine", "printer", "machine_name", "printer_name"},
    "feature": {"feature", "dimension", "feature_name", "critical_dimension", "characteristic"},
    "nominal_mm": {"nominal", "nominal_mm", "target", "target_mm", "required"},
    "measured_mm": {"measured", "measured_mm", "actual", "actual_mm", "result"},
    "lower_tol_mm": {"lower_tol", "lower_tolerance", "lsl", "min"},
    "upper_tol_mm": {"upper_tol", "upper_tolerance", "usl", "max"},
    "date": {"date", "inspection_date", "inspected_at", "timestamp"},
    "operator": {"operator", "inspector", "technician"},
}

def map_columns(headers: list[str]) -> list[dict[str, Any]]:
    out=[]
    for h in headers:
        n=normalize_header(h)
        candidates=[field for field, aliases in FIELD_ALIASES.items() if n in aliases or any(a in n for a in aliases if len(a)>3)]
        out.append({"source_column": h, "normalized": n, "candidates": candidates, "status": "needs_confirmation" if len(candidates)!=1 else "suggested"})
    return out

@app.post("/v1/import/preview")
async def import_preview(file: UploadFile = File(...)):
    raw=await file.read()
    if len(raw)>5_000_000: raise HTTPException(413,"Inspection file exceeds 5 MB limit.")
    text=raw.decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(io.StringIO(text))
    headers=reader.fieldnames or []
    rows=[]
    for i,row in enumerate(reader):
        if i>=1000: break
        rows.append(row)
    return {"filename":file.filename,"content_sha256":hashlib.sha256(raw).hexdigest(),"columns":map_columns(headers),"row_count_preview":len(rows),"rows":rows[:10],"requires_confirmation":True,"provenance":{"source":"user_uploaded_record","synthetic":False}}

@app.post("/v1/geometry/step")
async def step_geometry(file: UploadFile = File(...)):
    raw=await file.read()
    if len(raw)>25_000_000: raise HTTPException(413,"Geometry exceeds 25 MB limit.")
    name=(file.filename or "").lower()
    if not name.endswith((".step",".stp")): raise HTTPException(415,"Only STEP/STP is accepted by this endpoint.")
    text=raw.decode("utf-8",errors="ignore")
    pts=[]
    for m in re.finditer(r"CARTESIAN_POINT\s*\([^;]*?\(\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*\)\s*\)", text, re.I|re.S):
        pts.append(tuple(float(v) for v in m.groups()))
    if not pts:
        return {"status":"unsupported","reason":"No Cartesian points could be extracted from this STEP file.","provenance":{"source":"STEP","method":"textual_cartesian_point_parser"}}
    a=np.array(pts); mins=a.min(axis=0); maxs=a.max(axis=0); dims=maxs-mins
    return {"status":"extracted_limited","units":"file_units_assumed_mm","point_count":len(pts),"bounding_box":{"min":mins.tolist(),"max":maxs.tolist(),"size":dims.tolist()},"feature_extraction":{"method":"vertex/bounding-box pass","topology_features":None,"status":"limited"},"provenance":{"source":"STEP","method":"CARTESIAN_POINT parser","warning":"Unit declaration and full BREP topology require a CAD kernel; no unit conversion or topology was invented."}}

@app.post("/v1/cv/measure")
async def measure(file: UploadFile = File(...)):
    data=await file.read()
    if len(data)>10_000_000: raise HTTPException(413,"Image exceeds 10 MB limit.")
    arr=np.frombuffer(data,np.uint8); image=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
    if image is None: raise HTTPException(415,"Unsupported image format")
    edges=cv2.Canny(image,50,150)
    lines=cv2.HoughLinesP(edges,1,np.pi/180,threshold=80,minLineLength=max(30,image.shape[1]//5),maxLineGap=10)
    count=0 if lines is None else len(lines)
    return {"status":"limited","features_detected":count,"measurement_mm":None,"confidence":"unknown","reason":"A physical scale/reference feature is required before pixels can become millimetres. Fabrient refuses silent scale inference.","provenance":{"source":"image","algorithm":"opencv-canny-hough","measurement_ground_truth":False}}

@app.post("/v1/agents/run")
def run_agents(x: AgentRequest):
    stages=["observe","understand","generate_options","prioritize","act","measure","evaluate","learn","update"]
    return {"status":"bounded_plan","project_id":x.project_id,"objective":x.objective,"max_iterations":x.max_iterations,
            "agents":["context_evidence","physics","deterministic_validation","measurement_cv","system_identification","residual_ml","uncertainty_risk_gate","experiment_selection","critic"],
            "loop":stages,"approval_gates":["physical_experiment","acceptance_refusal_override"],
            "note":"This endpoint emits a bounded execution plan. It does not autonomously fabricate evidence or execute physical actions."}
