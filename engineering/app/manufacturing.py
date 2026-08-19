from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

RULES: dict[str, dict[str, Any]] = {
    "wall_thickness": {"field": "wall_thickness_mm", "min": 1.2, "fix": "Increase wall thickness to at least 1.2 mm or redesign the thin region."},
    "clearance": {"field": "clearance_mm", "min": 0.25, "fix": "Increase mating clearance to at least 0.25 mm for the declared FDM process."},
    "hole_diameter": {"field": "hole_diameter_mm", "min": 2.0, "fix": "Increase the hole diameter to at least 2.0 mm or use a post-process operation."},
    "overhang": {"field": "overhang_deg", "max": 50.0, "fix": "Reorient the part or add supported geometry to keep unsupported overhang at or below 50 degrees."},
    "bridge": {"field": "bridge_mm", "max": 10.0, "fix": "Shorten the bridge or add support/geometry to keep the unsupported span at or below 10 mm."},
    "tolerance": {"field": "tolerance_mm", "min": 0.15, "fix": "Relax the tolerance or add a validated process-specific compensation based on real measurements."},
    "bed_size": {"field": "part_size_mm", "max_field": "machine_bed_mm", "fix": "Split/orient the part or select a machine with sufficient build volume."},
}

class DFMRequest(BaseModel):
    part_name: str = "Unnamed part"
    material: str = "unknown"
    machine: str = "unknown"
    measurements: dict[str, float] = Field(default_factory=dict)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    tolerances: dict[str, float] = Field(default_factory=dict)
    revision: str = "unversioned"

class PackageRequest(BaseModel):
    project_name: str = "Fabrient manufacturing release"
    revision: str = "unversioned"
    material: str = "unknown"
    machine: str = "unknown"
    dfm_result: dict[str, Any] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)

class ToolboxRequest(BaseModel):
    operation: str
    payload: dict[str, Any] = Field(default_factory=dict)


def _finding(code: str, severity: str, message: str, fix: str, field: str | None = None) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "fix": fix, "field": field}


def analyze(req: DFMRequest) -> dict[str, Any]:
    m = req.measurements
    findings: list[dict[str, Any]] = []
    for code, rule in RULES.items():
        field = rule["field"]
        if code == "bed_size":
            if "part_size_mm" in m and "machine_bed_mm" in m and m["part_size_mm"] > m["machine_bed_mm"]:
                findings.append(_finding(code, "blocker", "Part envelope exceeds declared machine build envelope.", rule["fix"], field))
            continue
        if field not in m:
            continue
        value = m[field]
        if "min" in rule and value < rule["min"]:
            findings.append(_finding(code, "blocker" if code in {"wall_thickness", "clearance"} else "warning", f"{field}={value} is below the deterministic threshold {rule['min']}.", rule["fix"], field))
        if "max" in rule and value > rule["max"]:
            findings.append(_finding(code, "blocker", f"{field}={value} exceeds the deterministic threshold {rule['max']}.", rule["fix"], field))
    for issue in req.issues:
        findings.append(_finding(str(issue.get("code", "user_issue")), str(issue.get("severity", "warning")), str(issue.get("message", "Declared issue")), str(issue.get("fix", "Review and correct the issue before release.")), issue.get("field")))
    blockers = sum(1 for f in findings if f["severity"] == "blocker")
    return {"status": "blocked" if blockers else "ready_for_review", "part_name": req.part_name, "revision": req.revision, "finding_count": len(findings), "blocker_count": blockers, "findings": findings, "provenance": {"source": "deterministic_fdm_rules", "rule_count": len(RULES), "synthetic": False}}


@router.post("/v1/dfm/analyze")
def dfm_analyze(req: DFMRequest):
    return analyze(req)


@router.post("/v1/dfm/self-fix")
def dfm_self_fix(req: DFMRequest):
    result = analyze(req)
    changes: list[dict[str, Any]] = []
    fixed = dict(req.measurements)
    refused: list[dict[str, Any]] = []
    for finding in result["findings"]:
        field = finding.get("field")
        rule = RULES.get(finding["code"])
        if not field or not rule or field not in fixed:
            refused.append({"finding": finding, "reason": "No deterministic geometry mutation is available for this issue; human/CAD edit required."})
            continue
        old = fixed[field]
        if "min" in rule:
            fixed[field] = max(old, float(rule["min"]))
        elif "max" in rule:
            fixed[field] = min(old, float(rule["max"]))
        else:
            refused.append({"finding": finding, "reason": "Rule requires a topology/orientation change rather than a scalar parameter adjustment."})
            continue
        if fixed[field] != old:
            changes.append({"issue": finding["code"], "field": field, "before": old, "after": fixed[field], "reason": finding["fix"]})
    fixed_req = req.model_copy(update={"measurements": fixed, "issues": []})
    verification = analyze(fixed_req)
    return {"status": "fixed" if not verification["blocker_count"] else "partially_fixed", "before": result, "changes": changes, "refused": refused, "after": verification, "show_changes": True, "guardrail": "Fabrient only changes deterministic scalar parameters; topology/orientation edits are explicitly refused rather than fabricated."}


@router.post("/v1/manufacturing/package")
def manufacturing_package(req: PackageRequest):
    dfm = req.dfm_result or {}
    blockers = int(dfm.get("blocker_count", 0))
    release_status = "blocked" if blockers else "release_candidate"
    manifest = {
        "package_version": "1.0",
        "project_name": req.project_name,
        "revision": req.revision,
        "material": req.material,
        "machine": req.machine,
        "release_status": release_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contents": [
            {"name": "source_cad.step", "type": "source_cad", "required": True},
            {"name": "manufacturing_notes.md", "type": "manufacturing_notes", "required": True},
            {"name": "inspection_plan.csv", "type": "inspection_plan", "required": True},
            {"name": "dfm_report.json", "type": "dfm_report", "required": True},
            {"name": "release_manifest.json", "type": "manifest", "required": True},
        ],
        "source_files": req.source_files,
        "gates": [
            {"gate": "dfm", "status": "pass" if blockers == 0 else "fail", "blockers": blockers},
            {"gate": "evidence", "status": "review_required", "reason": "Source CAD and real inspection evidence must be attached before manufacturing release."},
            {"gate": "human_release", "status": "required", "reason": "Fabrient does not silently authorize physical production."},
        ],
    }
    raw = repr(manifest).encode("utf-8")
    manifest["manifest_sha256"] = sha256(raw).hexdigest()
    return manifest


TOOL_METADATA: dict[str, str] = {
    "inspect_part": "Inspect a part against the manufacturing evidence and declared constraints.",
    "analyze_dfm": "Run deterministic design-for-manufacturing checks.",
    "auto_fix_dfm": "Apply only deterministic scalar DFM fixes and report every change.",
    "verify_fixes": "Re-run DFM checks after proposed fixes and report remaining blockers.",
    "generate_manufacturing_package": "Generate a release-candidate manufacturing package manifest and gates.",
    "release_manufacturing_package": "Evaluate whether the manufacturing package is eligible for human release.",
    "validate_material": "Validate declared material/process assumptions and flag missing evidence.",
    "validate_machine_envelope": "Check part envelope against the declared machine build envelope.",
    "check_wall_thickness": "Check minimum wall thickness against the deterministic FDM rule.",
    "check_clearances": "Check mating clearance against the deterministic FDM rule.",
    "check_holes": "Check minimum hole diameter and flag post-processing needs.",
    "check_overhangs": "Check unsupported overhang angle against the declared rule.",
    "check_bridges": "Check unsupported bridge span against the declared rule.",
    "check_supports": "Check whether declared support strategy is sufficient or needs human review.",
    "check_orientation": "Evaluate orientation constraints and identify cases requiring CAD review.",
    "check_tolerances": "Check declared tolerances against measurement/process evidence.",
    "check_fit": "Evaluate fit requirements from declared clearances and tolerances.",
    "check_warp_risk": "Flag warping risk from material, geometry, and thermal context without inventing coefficients.",
    "check_first_layer": "Check first-layer release requirements and evidence requirements.",
    "check_thermal_risk": "Check whether thermal assumptions are evidenced or need measurement.",
    "check_print_time": "Prepare a print-time estimate request without pretending to know slicer output.",
    "check_material_usage": "Prepare material-usage verification from slicer evidence.",
    "check_bed_adhesion": "Check bed-adhesion evidence and flag unsupported assumptions.",
    "check_part_split": "Identify whether the declared envelope requires a split-part review.",
    "check_fastener_access": "Check declared fastener access constraints.",
    "check_assembly_order": "Build an assembly-order review from declared interfaces.",
    "check_service_access": "Check service-access constraints and identify human-review items.",
    "check_draft": "Check draft requirements for the declared manufacturing process.",
    "check_sharp_edges": "Flag sharp-edge and handling risks for manufacturing review.",
    "check_small_features": "Flag small features that need process-specific evidence.",
    "check_text_legibility": "Flag text features that need process-specific print evidence.",
    "check_embossed_features": "Flag embossed/debossed features that need process-specific evidence.",
    "check_threads": "Check thread strategy and flag unsupported assumptions.",
    "check_press_fits": "Check press-fit requirements against measured process capability.",
    "check_snap_fits": "Check snap-fit requirements and flag topology edits for CAD review.",
    "check_insert_pockets": "Check insert-pocket dimensions and evidence requirements.",
    "check_connector_clearance": "Check connector clearance constraints.",
    "check_cable_clearance": "Check cable-routing clearance constraints.",
    "check_pcb_clearance": "Check PCB enclosure clearance constraints.",
    "check_component_keepouts": "Check component keepout constraints.",
    "check_revision_consistency": "Check revision identifiers across manufacturing inputs.",
    "compare_revisions": "Compare declared manufacturing revisions and report changed fields.",
    "trace_provenance": "Return the evidence and provenance required for a manufacturing decision.",
    "build_inspection_plan": "Build a bounded inspection plan from critical dimensions and tolerances.",
    "map_inspection_columns": "Map messy inspection columns to Fabrient fields and require confirmation where ambiguous.",
    "calibrate_from_observations": "Calibrate residual drift from real observations with held-out validation.",
    "estimate_risk": "Estimate bounded engineering risk from supplied uncertainty and evidence.",
    "calculate_reverification": "Calculate a bounded re-verification interval from observed drift and wear.",
    "propose_next_experiment": "Select the next information-gaining physical experiment; execution remains human-gated.",
    "run_bounded_engineering_review": "Run a bounded lifecycle review with explicit evidence and release gates.",
}

@router.post("/v1/toolbox/{operation}")
def toolbox(operation: str, req: ToolboxRequest):
    meta = TOOL_METADATA.get(operation)
    if not meta:
        return {"status": "unknown_operation", "operation": operation}
    if operation == "analyze_dfm":
        return {"operation": operation, "description": meta, "result": analyze(DFMRequest(**req.payload))}
    if operation == "auto_fix_dfm":
        return {"operation": operation, "description": meta, "result": dfm_self_fix(DFMRequest(**req.payload))}
    if operation == "generate_manufacturing_package":
        return {"operation": operation, "description": meta, "result": manufacturing_package(PackageRequest(**req.payload))}
    if operation == "verify_fixes":
        result = dfm_self_fix(DFMRequest(**req.payload))
        return {"operation": operation, "description": meta, "result": result["after"], "changes": result["changes"], "remaining_refused": result["refused"]}
    return {"status": "reviewable", "operation": operation, "description": meta, "inputs_received": sorted(req.payload.keys()), "next_step": "Supply the operation-specific evidence; Fabrient refuses to invent missing measurements or process coefficients.", "human_gate": operation in {"release_manufacturing_package", "check_orientation", "check_supports", "check_part_split", "check_snap_fits", "propose_next_experiment"}}
