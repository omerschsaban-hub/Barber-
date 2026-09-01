from __future__ import annotations

import csv, io, math
from typing import Any
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_absolute_error

router = APIRouter(prefix="/v1")

class SystemObservation(BaseModel):
    predicted_mm: float
    measured_mm: float
    layer_height_mm: float = Field(gt=0)
    print_speed_mm_s: float = Field(gt=0)
    nozzle_temp_c: float = Field(gt=0)
    ambient_temp_c: float = 23
    humidity_pct: float = Field(default=50, ge=0, le=100)
    axis: int = Field(default=0, ge=0, le=2)

class SystemIdentificationRequest(BaseModel):
    observations: list[SystemObservation] = Field(default_factory=list)

class ReportMeasurement(BaseModel):
    feature: str
    nominal_mm: float
    measured_mm: float | None
    lower_tol_mm: float | None = None
    upper_tol_mm: float | None = None
    result: str = "indeterminate"

class InspectionReport(BaseModel):
    serial: str
    gauge_name: str
    machine: str
    operator: str | None = None
    inspected_at: str
    acceptance_criteria: str
    measurements: list[ReportMeasurement]
    provenance: dict[str, Any] = {}

class ResidualPredictionRequest(BaseModel):
    physics_sigma_mm: float = Field(ge=0)
    measurement_sigma_mm: float = Field(ge=0)
    model_sigma_mm: float = Field(ge=0)
    residuals_mm: list[float] = []
    n_real_observations: int = Field(ge=0)

class AgentGraphRequest(BaseModel):
    project_id: str
    max_iterations: int = Field(default=5, ge=1, le=20)
    approval_required: bool = True

@router.post("/system-identification")
def system_identification(req: SystemIdentificationRequest):
    if len(req.observations) < 8:
        return {"status":"limited","reason":"At least 8 real observations are required before estimating machine/process coefficients.","n":len(req.observations)}
    y=np.array([o.measured_mm-o.predicted_mm for o in req.observations])
    X=np.array([[o.layer_height_mm,o.print_speed_mm_s,o.nozzle_temp_c,o.ambient_temp_c,o.humidity_pct,o.axis] for o in req.observations],float)
    model=Ridge(alpha=1.0).fit(X,y)
    loo=cross_val_predict(Ridge(alpha=1.0),X,y,cv=LeaveOneOut())
    mae=float(mean_absolute_error(y,loo))
    residual=y-model.predict(X)
    sigma=float(max(np.std(residual,ddof=1),1e-6))
    return {"status":"validated" if len(req.observations)>=12 else "limited","n":len(req.observations),"features":["layer_height_mm","print_speed_mm_s","nozzle_temp_c","ambient_temp_c","humidity_pct","axis"],"coefficients":model.coef_.tolist(),"intercept_mm":float(model.intercept_),"held_out_mae_mm":mae,"residual_sigma_mm":sigma,"provenance":{"source":"real_observations","validation":"leave_one_out","model":"ridge-system-id-v1"}}

@router.post("/residual-uncertainty")
def residual_uncertainty(req: ResidualPredictionRequest):
    if req.n_real_observations < 3:
        return {"status":"not_calibrated","interval":None,"reason":"No uncertainty claim is allowed before real observations exist."}
    base=math.sqrt(req.physics_sigma_mm**2+req.measurement_sigma_mm**2+req.model_sigma_mm**2)
    empirical=float(np.std(req.residuals_mm,ddof=1)) if len(req.residuals_mm)>1 else 0.0
    sigma=math.sqrt(base**2+empirical**2)
    return {"status":"validated" if req.n_real_observations>=12 else "limited","sigma_mm":sigma,"interval_95_mm":[-1.96*sigma,1.96*sigma],"components":{"physics":req.physics_sigma_mm,"measurement":req.measurement_sigma_mm,"model":req.model_sigma_mm,"empirical_residual":empirical},"provenance":{"source":"real_observations","method":"quadrature_plus_empirical_residual"}}

@router.post("/inspection-report/csv")
def inspection_csv(report: InspectionReport):
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["serial","gauge","machine","operator","inspected_at","feature","nominal_mm","measured_mm","lower_tol_mm","upper_tol_mm","result"])
    for m in report.measurements:
        w.writerow([report.serial,report.gauge_name,report.machine,report.operator or "",report.inspected_at,m.feature,m.nominal_mm,m.measured_mm if m.measured_mm is not None else "",m.lower_tol_mm if m.lower_tol_mm is not None else "",m.upper_tol_mm if m.upper_tol_mm is not None else "",m.result])
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="inspection-{report.serial}.csv"'})

@router.post("/inspection-report/pdf")
def inspection_pdf(report: InspectionReport):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        raise HTTPException(503,"PDF dependency is not installed")
    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=A4); width,height=A4; y=height-50
    c.setFont("Helvetica-Bold",15); c.drawString(40,y,"FABRIENT — INSPECTION RECORD"); y-=25
    c.setFont("Helvetica",9)
    for label,value in [("Serial",report.serial),("Gauge",report.gauge_name),("Machine",report.machine),("Operator",report.operator or "—"),("Inspected",report.inspected_at),("Acceptance",report.acceptance_criteria)]:
        c.drawString(40,y,f"{label}: {value}"); y-=14
    y-=8; c.setFont("Helvetica-Bold",9); c.drawString(40,y,"Feature"); c.drawString(160,y,"Nominal"); c.drawString(220,y,"Measured"); c.drawString(290,y,"Limits"); c.drawString(430,y,"Result"); y-=15; c.setFont("Helvetica",8)
    for m in report.measurements:
        if y<55: c.showPage(); y=height-50
        limits=f"{m.lower_tol_mm if m.lower_tol_mm is not None else ''} / {m.upper_tol_mm if m.upper_tol_mm is not None else ''}"
        c.drawString(40,y,m.feature[:18]); c.drawString(160,y,f"{m.nominal_mm:g}"); c.drawString(220,y,"—" if m.measured_mm is None else f"{m.measured_mm:g}"); c.drawString(290,y,limits[:22]); c.drawString(430,y,m.result); y-=13
    y-=10; c.setFont("Helvetica",7); c.drawString(40,y,"Provenance: " + str(report.provenance)[:140]); c.save(); buf.seek(0)
    return Response(buf.read(),media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="inspection-{report.serial}.pdf"'})

@router.post("/agent-graph")
def agent_graph(req: AgentGraphRequest):
    agents=[
      ("context_evidence","Collect only relevant provenance-backed evidence"),
      ("physics","Generate baseline prediction from deterministic equations"),
      ("deterministic_validation","Validate units, ranges, tolerances and gates"),
      ("measurement_cv","Extract measurements only when scale is evidenced"),
      ("system_identification","Fit machine/process effects only from real observations"),
      ("residual_ml","Fit interpretable residual model with held-out validation"),
      ("uncertainty_risk_gate","Combine uncertainty and refuse unsupported conclusions"),
      ("experiment_selection","Select the next physical experiment by information value"),
      ("critic","Attempt to falsify assumptions before a recommendation")]
    edges=[{"from":agents[i][0],"to":agents[i+1][0]} for i in range(len(agents)-1)]
    return {"project_id":req.project_id,"bounded":True,"max_iterations":req.max_iterations,"nodes":[{"id":a,"label":b,"approval_required":req.approval_required and a in {"measurement_cv","experiment_selection"}} for a,b in agents],"edges":edges,"loop":["OBSERVE","UNDERSTAND","GENERATE_OPTIONS","PRIORITIZE","ACT","MEASURE","EVALUATE","LEARN","UPDATE","REPEAT"],"prohibited":["fabricated_measurements","fabricated_confidence","automatic_tolerance_override","unbounded_execution"]}
