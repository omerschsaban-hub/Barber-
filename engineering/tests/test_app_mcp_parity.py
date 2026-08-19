from pathlib import Path

from fastapi.testclient import TestClient

from app.composed import app

client = TestClient(app)
MCP = Path(__file__).parents[2] / "services" / "mcp" / "server.py"
MCP_SOURCE = MCP.read_text(encoding="utf-8")


def test_app_exposes_core_ui_engineering_capabilities():
    routes = {route.path for route in app.routes}
    required = {
        "/v1/predict",
        "/v1/import/preview",
        "/v1/reverification",
        "/v1/next-experiment",
        "/v1/geometry/step",
        "/v1/cv/measure-real",
        "/v1/cv/measure-real-json",
        "/v1/cv/detect-line-candidates-json",
        "/v1/sim2real/run",
        "/v1/sim2real/compare",
        "/v1/sim2real/calibrate-and-run",
        "/v1/agents/fleet",
        "/v1/agent-graph",
        "/v1/system-identification",
        "/v1/residual-uncertainty",
        "/v1/inspection-report/csv",
        "/v1/inspection-report/pdf",
        "/v1/risk-map",
        "/v1/dfm/analyze",
        "/v1/dfm/self-fix",
        "/v1/manufacturing/package",
        "/v1/manufacturing/build-guide",
    }
    assert required <= routes


def test_mcp_contains_every_core_engineering_capability():
    required_names = [
        "physics_predict", "simulation_run", "calibration_fit", "uncertainty_calculate",
        "reverification_calculate", "next_experiment", "cad_step_extract",
        "cv_measure", "cv_measure_real_json", "cv_detect_line_candidates",
        "sim2real_run", "sim2real_compare", "sim2real_calibrate_and_run",
        "agent_fleet_run", "system_identification", "residual_uncertainty",
        "agent_graph", "inspection_report_csv", "inspection_report_pdf",
        "risk_map", "dfm_analyze", "dfm_self_fix", "manufacturing_package",
        "physical_build_guide", "release_manufacturing_package",
    ]
    for name in required_names:
        assert f'("{name}"' in MCP_SOURCE, name


def test_risk_map_never_turns_missing_evidence_into_acceptance():
    response = client.post("/v1/risk-map", json={"findings": [], "uncertainty_sigma_mm": 0.3, "tolerance_mm": 0.4})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "computed"
    assert body["risk_map"][0]["level"] == "high"
    assert body["provenance"]["invented_measurements"] is False
    assert "physical acceptance" in body["provenance"]["claim_boundary"]
