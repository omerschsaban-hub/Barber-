from __future__ import annotations

import io, hashlib
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_absolute_error

router = APIRouter(prefix="/v1/final", tags=["final-engineering"])

class SystemIDObservation(BaseModel):
    machine_id: str
    predicted_mm: float
    measured_mm: float
    temperature_c: float = Field(ge=-50, le=150)
    humidity_pct: float = Field(ge=0, le=100)
    layer_height_mm: float = Field(gt=0, le=2)
    speed_mm_s: float = Field(gt=0, le=1000)

class SystemIDRequest(BaseModel):
    observations: list[SystemIDObservation]
    min_points: int = Field(default=6, ge=4, le=10000)

class RiskRequest(BaseModel):
    nominal_mm: float = Field(gt=0)
    predicted_mm: float
    uncertainty_mm: float = Field(ge=0)
    lower_tol_mm: float
    upper_tol_mm: float

class ImportConfirm(BaseModel):
    filename: str
    content_sha256: str
    mapping: dict[str, str]
    rows: list[dict[str, Any]] = Field(max_length=5000)
    unit: str = "mm"

class AgentStep(BaseModel):
    objective: str
    max_iterations: int = Field(default=5, ge=1, le=20)
    budget: float = Field(default=0, ge=0)
    approved: bool = False


def _risk(nominal: float, predicted: float, sigma: float, lo: float, hi: float):
    if hi <= lo:
        raise HTTPException(422, "Upper tolerance must exceed lower tolerance.")
    interval = (predicted, predicted) if sigma <= 0 else (predicted - 1.96*sigma, predicted + 1.96*sigma)
    lower, upper = nominal + lo, nominal + hi
    band = upper - lower
    consumed = min(10.0, max(0.0, (3.92*sigma) / band))
    outside = interval[0] < lower or interval[1] > upper
    level = "refuse" if outside else ("high" if consumed >= .75 else ("medium" if consumed >= .40 else "low"))
    return {"risk_level": level, "interval_95_mm": list(interval), "tolerance_consumed_fraction": consumed,
            "supported": level != "refuse", "reason": "Prediction interval exceeds acceptance bounds." if outside else "Prediction interval remains inside acceptance bounds."}

@router.post("/risk")
def computed_risk(x: RiskRequest):
    return {"status": "ok", "result": _risk(x.nominal_mm, x.predicted_mm, x.uncertainty_mm, x.lower_tol_mm, x.upper_tol_mm),
            "provenance": {"source": "deterministic_engineering", "uncertainty": "explicit input; no fabricated confidence"}}

@router.post("/system-identification")
def system_identification(x: SystemIDRequest):
    if len(x.observations) < x.min_points:
        return {"status": "limited", "reason": f"Need {x.min_points} real observations; received {len(x.observations)}.", "synthetic_data": False}
    machines = sorted({o.machine_id for o in x.observations})
    if len(machines) != 1:
        return {"status": "refused", "reason": "Identify one machine at a time to avoid conflating machine effects.", "machines": machines}
    y = np.array([o.measured_mm-o.predicted_mm for o in x.observations])
    X = np.array([[o.temperature_c, o.humidity_pct, o.layer_height_mm, o.speed_mm_s] for o in x.observations], dtype=float)
    model = Ridge(alpha=1.0).fit(X, y)
    cv = cross_val_predict(Ridge(alpha=1.0), X, y, cv=LeaveOneOut())
    mae = float(mean_absolute_error(y, cv))
    sigma = float(max(np.std(y-cv, ddof=1), 1e-9))
    baseline_sigma = float(np.std(y, ddof=1)) if len(y) > 1 else 0
    status = "validated" if baseline_sigma > 0 and mae < baseline_sigma * .9 else "limited"
    return {"status": status, "machine_id": machines[0], "n": len(y),
            "coefficients": dict(zip(["temperature_c","humidity_pct","layer_height_mm","speed_mm_s"], model.coef_.tolist())),
            "intercept_mm": float(model.intercept_), "held_out_mae_mm": mae, "uncertainty_sigma_mm": sigma,
            "provenance": {"training": "real observations only", "validation": "leave-one-out", "model": "ridge-system-id-v1"}}

@router.post("/import/confirm")
def confirm_import(x: ImportConfirm):
    required = {"serial", "feature", "measured_mm"}
    missing = required-set(x.mapping.values())
    if missing:
        raise HTTPException(422, f"Cannot ingest: required mappings missing: {sorted(missing)}")
    if x.unit.lower() not in {"mm", "millimeter", "millimeters"}:
        raise HTTPException(422, "Only explicit millimetre ingestion is enabled in v1; convert before import.")
    digest = hashlib.sha256((x.filename+str(x.rows)+str(x.mapping)).encode()).hexdigest()
    return {"status":"confirmed", "row_count":len(x.rows), "content_sha256":x.content_sha256, "confirmation_hash":digest,
            "mapping":x.mapping, "synthetic":False}

@router.post("/inspection-record/pdf")
def inspection_pdf(record: dict[str, Any]):
    required = ["serial","machine","date","acceptance_criteria","measurements"]
    missing=[k for k in required if k not in record]
    if missing: raise HTTPException(422, f"Missing inspection record fields: {missing}")
    styles=getSampleStyleSheet()
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,title=f"Fabrient inspection {record['serial']}")
    story=[Paragraph("Fabrient Inspection Record", styles["Title"]), Spacer(1,10)]
    meta=[[k.replace('_',' ').title(), str(record[k])] for k in required if k != "measurements"]
    story.append(Table(meta)); story.append(Spacer(1,12))
    rows=[["Feature","Nominal (mm)","Measured (mm)","Lower","Upper","Decision"]]
    for m in record["measurements"]:
        rows.append([str(m.get("feature","")),str(m.get("nominal_mm","")),str(m.get("measured_mm","")),str(m.get("lower_tol_mm","")),str(m.get("upper_tol_mm","")),str(m.get("status",""))])
    t=Table(rows,repeatRows=1); t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.5,colors.black),("BACKGROUND",(0,0),(-1,0),colors.lightgrey)])); story.append(t)
    story.append(Spacer(1,12)); story.append(Paragraph("Measured evidence only. This is not a certification unless the user's quality system separately establishes that authority.", styles["BodyText"]))
    doc.build(story); buf.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=inspection-{record['serial']}.pdf"})

@router.post("/agent/step")
def bounded_agent_step(x: AgentStep):
    if not x.approved:
        return {"status":"approval_required","action":"none","reason":"Engineering actions remain human-approved in v1.","iterations":0}
    return {"status":"planned","iterations":min(x.max_iterations,4),"budget":x.budget,
            "allowed_actions":["observe_real_measurements","validate_provenance","estimate_uncertainty","propose_next_experiment"],
            "next_action":"observe_real_measurements","rollback":"no external physical action is executed automatically"}
