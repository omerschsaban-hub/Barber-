from fastapi.testclient import TestClient

from app.composed import app


client = TestClient(app)


def test_dfm_without_geometry_or_measurements_is_blocked():
    response = client.post("/v1/dfm/analyze", json={"part_name": "future_smartphone_enclosure"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["blocker_count"] >= 1
    assert "validated CAD geometry or operation-specific measurements" in body["missing_evidence"]


def test_empty_build_guide_is_blocked():
    response = client.post("/v1/manufacturing/build-guide", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert "validated source CAD" in body["missing_evidence"]
    assert "declared material" in body["missing_evidence"]
    assert "declared machine" in body["missing_evidence"]


def test_release_gate_cannot_approve_without_source_cad_and_real_inspection():
    response = client.post("/v1/toolbox/release_manufacturing_package", json={"operation": "release_manufacturing_package", "payload": {"dfm_result": {"blocker_count": 0}}})
    assert response.status_code == 200
    body = response.json()
    assert body["eligible"] is False
    assert body["package"]["release_status"] == "blocked"
    assert body["package"]["gates"][1]["status"] == "blocked"
