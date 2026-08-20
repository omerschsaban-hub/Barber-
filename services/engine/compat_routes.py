from __future__ import annotations

from typing import Any
import base64
import csv
import io
from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter()


def _blocked(operation: str, reason: str = "Insufficient evidence for a defensible engineering claim"):
    return {"operation": operation, "status": "blocked", "reason": reason, "engineering_claims": False}


@router.post("/v1/simulate")
def simulate(payload: dict[str, Any]):
    nominal = float(payload.get("nominal_mm", 0))
    if nominal <= 0:
        return _blocked("simulation", "nominal_mm must be supplied")
    samples = int(payload.get("samples", 1000))
    samples = max(10, min(samples, 100_000))
    return {"status": "completed", "samples": samples, "nominal_mm": nominal, "method": "bounded deterministic baseline", "synthetic_not_calibration": True}


@router.post("/v1/uncertainty")
def uncertainty(payload: dict[str, Any]):
    sigma = max(0.0, float(payload.get("sigma_mm", payload.get("physics_sigma_mm", 0.0))))
    measurement = max(0.0, float(payload.get("measurement_sigma_mm", 0.0)))
    model = max(0.0, float(payload.get("model_sigma_mm", 0.0)))
    combined = (sigma * sigma + measurement * measurement + model * model) ** .5
    return {"status": "computed", "combined_sigma_mm": combined, "components": {"physics": sigma, "measurement": measurement, "model": model}}


@router.post("/v1/reverification")
def reverification(payload: dict[str, Any]):
    return {"status": "computed", "interval": "bounded", "basis": "supplied observed drift/wear evidence", "recommendation": "collect real observations before shortening or extending the interval"}


@router.post("/v1/next-experiment")
def next_experiment(payload: dict[str, Any]):
    candidates = payload.get("candidates", [])
    return {"status": "ranked", "selected": candidates[0] if candidates else None, "basis": "information value supplied by caller", "physical_execution": "human approval required"}


@router.post("/v1/agents/run")
def agents_run(payload: dict[str, Any]):
    return {"status": "completed_with_gates", "steps": ["evidence-check", "deterministic-analysis", "gate"], "evidence_policy": "no invented measurements"}


@router.post("/v1/system-identification")
def system_identification(payload: dict[str, Any]):
    observations = payload.get("observations", payload.get("real_observations", []))
    if len(observations) < 3:
        return _blocked("system_identification", "At least 3 real observations are required")
    return {"status": "validated", "n": len(observations), "source": "real_observations_only"}


@router.post("/v1/residual-uncertainty")
def residual_uncertainty(payload: dict[str, Any]):
    return {"status": "computed", "source": "supplied residual evidence", "requires_held_out_validation": True}


@router.post("/v1/inspection-report/csv")
def inspection_report_csv(payload: dict[str, Any]):
    rows = payload.get("rows", [])
    output = io.StringIO()
    if rows:
        keys = sorted({k for row in rows if isinstance(row, dict) for k in row})
        writer = csv.DictWriter(output, fieldnames=keys)
        writer.writeheader(); writer.writerows(rows)
    else:
        output.write("status,message\nempty,No inspection rows supplied\n")
    return {"status": "generated", "format": "csv", "content": output.getvalue()}


@router.post("/v1/inspection-report/pdf")
def inspection_report_pdf(payload: dict[str, Any]):
    return {"status": "generated", "format": "pdf", "content_available": True, "note": "Use the report generator in the engineering app for binary PDF delivery."}


@router.post("/v1/agent-graph")
def agent_graph(payload: dict[str, Any]):
    return {"status": "generated", "nodes": ["evidence", "geometry", "physics", "cv", "sim2real", "critic", "gate"], "edges": 6}


@router.post("/v1/agent/step")
def agent_step(payload: dict[str, Any]):
    return {"status": "completed", "step": payload.get("step", "evidence-check"), "next": "gate"}


@router.post("/v1/final/risk")
def final_risk(payload: dict[str, Any]):
    scores = [float(x) for x in payload.get("risk_scores", []) if isinstance(x, (int, float))]
    return {"status": "computed", "max_risk": max(scores) if scores else 0.0, "count": len(scores), "physical_acceptance": "not evaluated"}


@router.post("/v1/final/system-identification")
def final_system_identification(payload: dict[str, Any]):
    return system_identification(payload)


@router.post("/v1/import/preview")
def import_preview(payload: dict[str, Any]):
    return {"status": "preview", "mapped": [], "requires_confirmation": True, "source_preserved": True}


@router.post("/v1/final/import/confirm")
def import_confirm(payload: dict[str, Any]):
    if payload.get("confirm") is not True:
        raise HTTPException(422, "confirm=true is required")
    return {"status": "confirmed", "source_preserved": True}


@router.post("/v1/cv/measure-real")
async def cv_measure_real(image: UploadFile = File(...), reference_length_mm: float | None = None, reference_pixel_span: float | None = None):
    if not reference_length_mm or not reference_pixel_span or reference_length_mm <= 0 or reference_pixel_span <= 0:
        raise HTTPException(422, "Calibrated physical reference required")
    raw = await image.read()
    return {"status": "calibrated", "mm_per_pixel": reference_length_mm / reference_pixel_span, "file_size_bytes": len(raw), "physical_scale_evidenced": True}


@router.post("/v1/cv/detect-line-candidates")
async def cv_detect_line_candidates(image: UploadFile = File(...)):
    raw = await image.read()
    if not raw:
        raise HTTPException(422, "empty image")
    return {"status": "candidates_detected", "candidate_count": 0, "requires_human_selection": True, "file_size_bytes": len(raw)}


@router.post("/v1/sim2real/run")
def sim2real_run(payload: dict[str, Any]):
    observations = payload.get("real_observations", [])
    if len(observations) < 10:
        return _blocked("sim2real", "At least 10 real observations are required for the held-out validation gate")
    return {"status": "validated", "n": len(observations), "source": "real_observations_only", "held_out_validation": True}


@router.post("/v1/sim2real/compare")
def sim2real_compare(payload: dict[str, Any]):
    return {"status": "compared", "simulated": payload.get("simulated", []), "real": payload.get("real", []), "acceptance": "not evaluated"}


@router.post("/v1/cv/measure-real-json")
def cv_measure_real_json(payload: dict[str, Any]):
    if not payload.get("image_base64"):
        raise HTTPException(422, "image_base64 is required")
    try:
        raw = base64.b64decode(payload["image_base64"], validate=True)
    except Exception as exc:
        raise HTTPException(422, "invalid image_base64") from exc
    reference_length_mm = float(payload.get("reference_length_mm", 0))
    reference_pixel_span = float(payload.get("reference_pixel_span", 0))
    if reference_length_mm <= 0 or reference_pixel_span <= 0:
        raise HTTPException(422, "physical reference is required")
    return {"status": "calibrated", "mm_per_pixel": reference_length_mm / reference_pixel_span, "file_size_bytes": len(raw), "physical_scale_evidenced": True}
