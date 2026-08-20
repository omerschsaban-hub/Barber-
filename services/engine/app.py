from __future__ import annotations

import base64
import io
import math
import re
import zipfile
from datetime import datetime, timezone
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

APP_VERSION = "0.2.0"
PHYSICS_VERSION = "fdm-shrinkage-2"
app = FastAPI(title="Fabrient Engineering Service", version=APP_VERSION)


class EngineeringInput(BaseModel):
    nominal_mm: float = Field(gt=0)
    material: str
    machine: str
    process: str = "FDM"
    nozzle_mm: float = Field(default=.4, gt=0)
    layer_height_mm: float = Field(default=.2, gt=0)
    bed_temp_c: float | None = None
    nozzle_temp_c: float | None = None
    infill_percent: float = Field(default=100, ge=0, le=100)
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


def fit(obs: list[CalibrationObservation]):
    if len(obs) < 3:
        return 0.0, None, "not_calibrated"
    residuals = np.array([o.measured_mm - o.predicted_mm for o in obs], dtype=float)
    std = float(residuals.std(ddof=1)) if len(obs) > 1 else 0.0
    return float(residuals.mean()), std, "validated" if len(obs) >= 10 else "limited"


def _step_bbox(raw: bytes) -> dict[str, Any]:
    """Conservative STEP text inspection: extract Cartesian point coordinates.
    This is intentionally not presented as a full BREP/solid parser.
    """
    text = raw.decode("utf-8", errors="ignore")
    pts = []
    pat = re.compile(r"CARTESIAN_POINT\s*\([^;]*?\(\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)\s*\)", re.I | re.S)
    for m in pat.finditer(text):
        try:
            pts.append(tuple(float(v) for v in m.groups()))
        except ValueError:
            pass
    if not pts:
        raise HTTPException(422, "STEP contains no readable CARTESIAN_POINT records; a full CAD kernel is required for this file.")
    arr = np.asarray(pts, dtype=float)
    lo = arr.min(axis=0); hi = arr.max(axis=0); size = hi - lo
    return {
        "parser": "conservative-cartesian-point-inspector",
        "point_count": int(len(arr)),
        "bbox_min_mm": [float(x) for x in lo],
        "bbox_max_mm": [float(x) for x in hi],
        "bbox_size_mm": [float(x) for x in size],
        "solid_topology_verified": False,
    }


def _payload_from_multipart(filename: str, raw: bytes, extra: dict[str, Any]) -> dict[str, Any]:
    result = dict(extra)
    result["filename"] = filename
    result["file_size_bytes"] = len(raw)
    result["step_inspection"] = _step_bbox(raw) if filename.lower().endswith((".step", ".stp")) else None
    return result


def _extract_payload(payload: dict[str, Any]) -> dict[str, Any]:
    p = dict(payload or {})
    encoded = p.pop("file_base64", None)
    if encoded:
        try:
            raw = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            raise HTTPException(422, "file_base64 must be valid base64") from exc
        if len(raw) > 25_000_000:
            raise HTTPException(413, "uploaded file exceeds 25 MB")
        return _payload_from_multipart(str(p.pop("filename", "upload.step")), raw, p)
    return p


@app.get("/health")
def health():
    return {"ok": True, "version": APP_VERSION, "physics_version": PHYSICS_VERSION}


@app.get("/v1/health")
def v1_health():
    return health()


@app.post("/v1/predict")
def predict(x: EngineeringInput):
    if x.tolerance_lower_mm > 0 or x.tolerance_upper_mm < 0:
        raise HTTPException(422, "Invalid tolerance convention")
    b, s = baseline(x)
    return {"baseline_mm": b, "residual_mm": 0, "predicted_mm": b,
            "interval_low_mm": b - 1.96*s, "interval_high_mm": b + 1.96*s,
            "status": "not_calibrated", "provenance": {"physics_version": PHYSICS_VERSION, "measured_data": False}}


@app.post("/v1/calibrate")
def calibration(obs: list[CalibrationObservation]):
    if not obs:
        raise HTTPException(400, "Real observations required")
    m, s, status = fit(obs)
    return {"residual_mean_mm": m, "residual_std_mm": s, "status": status, "n": len(obs), "source": "real_observations_only"}


@app.post("/v1/geometry/step")
async def geometry_step(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > 25_000_000:
        raise HTTPException(413, "uploaded file exceeds 25 MB")
    if not file.filename or not file.filename.lower().endswith((".step", ".stp")):
        raise HTTPException(422, "Expected STEP/STP file")
    return _payload_from_multipart(file.filename, raw, {})


@app.post("/v1/toolbox/{operation}")
def toolbox(operation: str, payload: dict[str, Any] | None = None):
    p = _extract_payload(payload or {})
    geometry = p.get("step_inspection")
    bbox = (geometry or {}).get("bbox_size_mm", [0, 0, 0])
    min_dim = min([x for x in bbox if x > 0], default=0)
    risks = []
    if not geometry:
        risks.append({"code": "NO_GEOMETRY_EVIDENCE", "severity": "high", "message": "No STEP geometry evidence supplied."})
    if geometry and not geometry.get("solid_topology_verified"):
        risks.append({"code": "TOPOLOGY_UNVERIFIED", "severity": "high", "message": "Conservative STEP inspection did not verify BREP topology."})
    if min_dim and min_dim < 0.8:
        risks.append({"code": "SMALL_FEATURE_RISK", "severity": "medium", "message": "Bounding-box minimum is below a conservative 0.8 mm feature threshold."})

    if operation in {"inspect_part", "analyze_dfm", "find_manufacturing_risks", "analyze_geometry", "extract_features", "score_manufacturability", "risk_map"}:
        return {"operation": operation, "geometry": geometry, "risks": risks,
                "manufacturability": "blocked" if risks else "provisional_pass",
                "evidence_gate": "blocked" if risks else "provisional"}
    if operation == "auto_fix_dfm":
        fixes = [{"risk": r["code"], "action": "request/full-CAD-kernel-fix", "status": "not_applied"} for r in risks]
        return {"operation": operation, "fixes": fixes, "auto_fix_applied": False,
                "reason": "This service cannot safely rewrite arbitrary STEP BREP geometry without a CAD kernel."}
    if operation == "verify_fixes":
        return {"operation": operation, "verified": not risks, "risks_remaining": risks,
                "requires_full_topology_check": bool(geometry and not geometry.get("solid_topology_verified"))}
    if operation == "build_inspection_plan":
        return {"inspection_plan": [{"item": "overall dimensions", "method": "calibrated physical measurement", "status": "required"},
                                     {"item": "fit/clearance", "method": "physical assembly test", "status": "required"},
                                     {"item": "visual/defect inspection", "method": "human inspection", "status": "required"}]}
    if operation == "trace_provenance":
        return {"provenance": {"generated_at": datetime.now(timezone.utc).isoformat(), "physics_version": PHYSICS_VERSION,
                                "geometry_evidence": bool(geometry), "real_measurements": bool(p.get("real_observations"))}}
    if operation == "release_manufacturing_package":
        return {"released": False, "status": "human_release_required", "reason": "Physical acceptance and full topology verification are not established by simulation alone."}
    return {"operation": operation, "status": "unsupported_operation", "message": "Endpoint is reachable; this operation is not implemented in the conservative engine."}


@app.post("/v1/dfm/analyze")
def dfm_analyze(payload: dict[str, Any]):
    return toolbox("analyze_dfm", payload)


@app.post("/v1/dfm/self-fix")
def dfm_self_fix(payload: dict[str, Any]):
    return toolbox("auto_fix_dfm", payload)


@app.post("/v1/manufacturing/package")
def manufacturing_package(payload: dict[str, Any]):
    p = _extract_payload(payload)
    analysis = toolbox("analyze_dfm", p)
    return {"release_candidate": True, "release_status": "HUMAN_RELEASE_REQUIRED",
            "analysis": analysis,
            "package_contents": ["engineering_summary.json", "dfm_findings.json", "inspection_plan.json", "release_notes.txt"],
            "physical_acceptance": "PENDING_REAL_BUILD",
            "sim2real_status": "BLOCKED_WITHOUT_REAL_OBSERVATIONS"}


@app.post("/v1/manufacturing/build-guide")
def build_guide(payload: dict[str, Any]):
    return {"title": "Fabrient Physical Build & Acceptance Guide",
            "steps": ["Confirm released revision and material/process settings.", "Manufacture one controlled sample.",
                      "Measure critical dimensions against the inspection plan.", "Perform physical fit/assembly checks.",
                      "Record observations and rerun sim-to-real calibration.", "Only then authorize production release."],
            "status": "guide_generated",
            "production_release": "not_authorized"}


@app.post("/v1/sim2real/calibrate-and-run")
def sim2real(payload: dict[str, Any]):
    observations = payload.get("real_observations") or []
    if len(observations) < 10:
        return {"status": "blocked", "reason": "Held-out sim-to-real validation requires real observations; none are invented by this service.", "required_minimum_observations": 10, "received": len(observations)}
    obs = [CalibrationObservation(**o) for o in observations]
    m, s, status = fit(obs)
    return {"status": "validated" if status == "validated" else "blocked", "residual_mean_mm": m, "residual_std_mm": s, "n": len(obs), "source": "real_observations_only"}


@app.post("/v1/agents/fleet")
def agent_fleet(payload: dict[str, Any]):
    return {"status": "completed_with_gates", "agents": ["geometry", "dfm", "physics", "cv", "sim2real", "critic"],
            "evidence_policy": "no invented measurements", "next": "provide real observations and full topology verification"}


@app.post("/v1/acceptance")
def acceptance(payload: dict[str, Any]):
    return {"accepted": False, "status": "HUMAN_PHYSICAL_ACCEPTANCE_REQUIRED", "reason": "Digital analysis cannot establish physical acceptance without measured build evidence."}


@app.post("/v1/cv/measure")
async def cv_measure(image: UploadFile = File(...), reference_length_mm: float | None = None):
    if not reference_length_mm or reference_length_mm <= 0:
        raise HTTPException(422, "Physical reference length required")
    import cv2
    data = await image.read(); arr = np.frombuffer(data, np.uint8); img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise HTTPException(422, "Invalid image")
    edges = cv2.Canny(img, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    px = max((cv2.boundingRect(c)[2] for c in contours), default=0)
    if not px:
        raise HTTPException(422, "No measurable feature found")
    return {"pixels": int(px), "reference_length_mm": reference_length_mm, "measurement_mm": None,
            "status": "needs_reference_pixel_span", "confidence": "limited"}


@app.post("/v1/import/preview")
def import_preview(payload: dict[str, Any]):
    return {"status": "preview", "columns": list((payload or {}).keys()), "requires_confirmation": True}


@app.post("/v1/inspection-report/pdf")
def inspection_pdf(payload: dict[str, Any]):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4)
    c.drawString(50, 800, "Fabrient Engineering Inspection Report")
    c.drawString(50, 780, "STATUS: HUMAN PHYSICAL ACCEPTANCE REQUIRED")
    c.drawString(50, 760, f"Generated: {datetime.now(timezone.utc).isoformat()}")
    c.save(); buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=inspection-report.pdf"})


@app.post("/v1/inspection-report/csv")
def inspection_csv(payload: dict[str, Any]):
    import csv
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(["item", "status", "evidence"])
    w.writerow(["physical_dimensions", "PENDING", "real measurement required"])
    w.writerow(["fit", "PENDING", "physical build required"])
    return StreamingResponse(io.BytesIO(buf.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=inspection-plan.csv"})
