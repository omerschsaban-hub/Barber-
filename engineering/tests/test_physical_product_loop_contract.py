from fastapi.testclient import TestClient

from app.composed import app
from app.main import EngineeringInput, physics
from app.manufacturing import DFMRequest, analyze, self_fix
from app.real_cv_sim2real import RealObservation, _fit

client = TestClient(app)


def test_deterministic_physics_is_repeatable():
    x = EngineeringInput(nominal_mm=40, material="PETG", machine="M1", process_temperature_c=245, nominal_shrinkage_pct=0.5, shrinkage_uncertainty_pct=0.1)
    assert physics(x) == physics(x)


def test_dfm_is_rule_based_and_fix_is_verified():
    req = DFMRequest(part_name="fixture", material="PETG", machine="FDM", revision="A", measurements={"wall_thickness_mm": 1.0, "clearance_mm": 0.1, "hole_diameter_mm": 2.5, "overhang_deg": 30, "bridge_mm": 5, "tolerance_mm": 0.2})
    before = analyze(req)
    result = self_fix(req)
    assert before["blocker_count"] >= 1
    assert result["after"]["blocker_count"] == 0
    assert result["show_changes"] is True
    assert result["guardrail"].startswith("Fabrient only changes deterministic")


def test_real_ml_requires_real_observations_and_held_out_validation():
    observations = [RealObservation(predicted_mm=10+i, measured_mm=10.02+i, machine_id="m1", feature_id=f"f{i}") for i in range(10)]
    fit = _fit(observations)
    assert fit["training_source"] == "real_observations_only"
    assert fit["status"] == "validated"
    assert fit["validation"] == "leave_one_out" or fit["validation"] == "group_kfold_by_machine_or_feature"


def test_quality_and_release_never_convert_missing_evidence_into_success():
    quality = client.post("/v1/quality/review", json={"project_name":"fixture","revision":"A","material":"PETG","machine":"FDM"})
    assert quality.status_code == 200
    assert quality.json()["status"] == "blocked"
    package = client.post("/v1/manufacturing/package", json={"project_name":"fixture","revision":"A","material":"PETG","machine":"FDM","dfm_result":{"blocker_count":0}})
    assert package.status_code == 200
    assert package.json()["release_status"] == "blocked"


def test_risk_map_is_deterministic_and_evidence_bound():
    r = client.post("/v1/risk-map", json={"findings":[{"id":"x","risk_score":0.8,"category":"fit","message":"clearance"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["risk_map"][0]["level"] == "critical"
    assert body["provenance"]["invented_measurements"] is False
