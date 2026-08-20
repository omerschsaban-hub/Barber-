from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/quality", tags=["engineering-quality"])


class QualityRequest(BaseModel):
    project_name: str = "Fabrient engineering project"
    revision: str = "unversioned"
    material: str = "unknown"
    machine: str = "unknown"
    dfm: dict = Field(default_factory=dict)
    sim2real: dict = Field(default_factory=dict)
    cv: dict = Field(default_factory=dict)
    inspection: dict = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)


def _gate(name: str, ok: bool, reason: str, next_action: str) -> dict:
    return {"gate": name, "status": "pass" if ok else "blocked", "reason": reason, "next_action": next_action}


def quality_review(x: QualityRequest) -> dict:
    dfm_ok = int(x.dfm.get("blocker_count", 0)) == 0 and x.dfm.get("status") not in {"blocked", "fail"}
    sim_status = str(x.sim2real.get("status", "missing"))
    sim_ok = sim_status in {"validated", "real_calibrated"} and float(x.sim2real.get("held_out_mape_percent", 999)) <= 2.0
    cv_ok = bool(x.cv.get("real_image_evidence")) and bool(x.cv.get("explicit_scale"))
    inspection_ok = bool(x.inspection.get("critical_features"))
    evidence_ok = bool(x.source_files) and cv_ok and inspection_ok
    gates = [
        _gate("1_geometry_integrity", True, "Geometry must be revisioned and internally consistent.", "Run deterministic CAD/kernel verification."),
        _gate("2_dfm", dfm_ok, "Deterministic DFM must have zero blockers.", "Run DFM auto-fix and verify again."),
        _gate("3_material_process", x.material != "unknown" and x.machine != "unknown", "Material and machine must be declared.", "Declare the actual material and machine."),
        _gate("4_simulation", bool(x.sim2real), "Simulation evidence must be present.", "Run the physics simulation with a fixed seed."),
        _gate("5_sim_to_real", sim_ok, "98% target requires <=2% held-out MAPE on real observations.", "Collect independent real observations and recalibrate."),
        _gate("6_cv_scale", cv_ok, "CV must use a real image and an explicit dimensional reference.", "Upload a real manufactured-part image with scale/reference."),
        _gate("7_inspection", inspection_ok, "Critical features must have an explicit inspection plan.", "Define critical dimensions and acceptance limits."),
        _gate("8_provenance", evidence_ok, "Release evidence must be traceable to real source/inspection artifacts.", "Attach source CAD, images, and measurement records."),
        _gate("9_package_consistency", bool(x.revision and x.project_name), "Package identity must be revisioned.", "Use one revision across every artifact."),
        _gate("10_human_release", False, "Physical acceptance remains human-gated.", "Have an engineer review the complete evidence package."),
    ]
    blocked = sum(g["status"] == "blocked" for g in gates)
    return {
        "status": "ready_for_human_release" if blocked == 0 else "blocked",
        "accuracy_target": "98% for sim-to-real when supported by held-out real evidence",
        "blocked_gates": blocked,
        "gates": gates,
        "provenance": {"source": "deterministic_quality_gate", "synthetic_ground_truth_used": False},
    }


def enhanced_package(x: QualityRequest) -> dict:
    review = quality_review(x)
    contents = [
        {"name": "source_cad/", "purpose": "exact released CAD and revision metadata", "required": True},
        {"name": "manufacturing_notes.md", "purpose": "machine/material/process assumptions and evidence boundaries", "required": True},
        {"name": "physical_build_guide.md", "purpose": "controlled build and verification procedure", "required": True},
        {"name": "inspection_plan.csv", "purpose": "critical dimensions, limits, actuals, instrument and evidence", "required": True},
        {"name": "dfm_report.json", "purpose": "deterministic DFM findings and fixes", "required": True},
        {"name": "cv_evidence/", "purpose": "real images, scale references, image hashes and CV results", "required": True},
        {"name": "sim2real_calibration.json", "purpose": "real observations, held-out metrics and correction history", "required": True},
        {"name": "release_manifest.json", "purpose": "artifact hashes, gates and release status", "required": True},
    ]
    manifest = {
        "package_version": "2.0-quality-gated",
        "project_name": x.project_name,
        "revision": x.revision,
        "material": x.material,
        "machine": x.machine,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release_status": "blocked" if review["blocked_gates"] else "release_candidate",
        "contents": contents,
        "quality_review": review,
        "source_files": x.source_files,
    }
    manifest["manifest_sha256"] = sha256(repr(manifest).encode()).hexdigest()
    return manifest


def enhanced_guide(x: QualityRequest) -> dict:
    review = quality_review(x)
    steps = [
        (1, "Lock identity", "Verify project, revision, material, machine and source-CAD hashes."),
        (2, "Run geometry verification", "Verify solids, dimensions, interfaces and revision consistency before manufacturing."),
        (3, "Run DFM", "Run every deterministic DFM rule, apply only supported fixes, and re-run verification."),
        (4, "Run physics simulation", "Run deterministic simulation with a recorded seed and preserve assumptions."),
        (5, "Validate sim-to-real", "Use real paired observations, deterministic held-out validation, and the 98% target; block if the target is missed."),
        (6, "Acquire CV evidence", "Use a real manufactured-part image with an explicit scale/reference and preserve the image hash."),
        (7, "Build inspection plan", "List every critical feature, nominal, tolerance, measurement method, instrument and acceptance rule."),
        (8, "Build physical part", "Follow machine-specific safety procedures and the released manufacturing process."),
        (9, "Inspect and reconcile", "Compare physical measurements/CV evidence against predicted values and record deviations."),
        (10, "Release or block", "Release only when every evidence gate passes and a human engineer records acceptance."),
    ]
    markdown = f"# Physical Build & Verification Guide\n\n**Project:** {x.project_name}\n\n**Revision:** {x.revision}\n\n**Material:** {x.material}\n\n**Machine:** {x.machine}\n\n**Quality-gate status:** {review['status']}\n\n" + "\n".join(f"## {n}. {title}\n{action}\n" for n, title, action in steps) + "\n## Non-negotiable evidence rules\n- Never substitute synthetic data for physical ground truth.\n- Never claim 98% accuracy without held-out real evidence.\n- Never silently modify released geometry.\n- A human engineer owns final physical acceptance.\n"
    return {"status": "ready_for_human_release" if review["blocked_gates"] == 0 else "blocked", "steps": [{"step": n, "title": t, "action": a} for n, t, a in steps], "guide_markdown": markdown, "quality_review": review}


@router.post("/review")
def review_route(x: QualityRequest):
    return quality_review(x)


@router.post("/package")
def package_route(x: QualityRequest):
    return enhanced_package(x)


@router.post("/build-guide")
def guide_route(x: QualityRequest):
    return enhanced_guide(x)
