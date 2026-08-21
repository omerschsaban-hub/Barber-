from fastapi.testclient import TestClient

from app.composed import app
from services.mcp.server import CAPABILITY_REGISTRY, TOOL_COUNT


def test_mcp_registry_is_complete_and_unique():
    names = [name for name, _, _ in CAPABILITY_REGISTRY]
    assert TOOL_COUNT == 100
    assert len(names) == 100
    assert len(set(names)) == 100


def test_every_registered_endpoint_is_mounted():
    mounted = {
        route.path
        for route in app.routes
        if hasattr(route, "path")
    }
    missing = sorted({path for _, _, path in CAPABILITY_REGISTRY} - mounted)
    assert not missing, f"Registered MCP endpoints missing from engineering app: {missing}"


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_core_deterministic_endpoints():
    client = TestClient(app)

    prediction = client.post(
        "/v1/predict",
        json={
            "nominal_mm": 100,
            "material": "PLA",
            "machine": "test-printer",
            "process_temperature_c": 210,
        },
    )
    assert prediction.status_code == 200
    assert "prediction_mm" in prediction.json()

    simulation = client.post(
        "/v1/simulate",
        json={
            "nominal_mm": 100,
            "shrinkage_pct": 0.5,
            "shrinkage_sigma_pct": 0.1,
            "temperature_c": 210,
            "temperature_sigma_c": 2,
            "n": 100,
            "seed": 42,
        },
    )
    assert simulation.status_code == 200
    assert simulation.json()["seed"] == 42

    uncertainty = client.post(
        "/v1/uncertainty",
        json={
            "physics_sigma_mm": 0.1,
            "measurement_sigma_mm": 0.05,
            "model_sigma_mm": 0.02,
            "n_observations": 3,
        },
    )
    assert uncertainty.status_code == 200
    assert uncertainty.json()["sigma_mm"] > 0


def test_multipart_upload_routes_reject_invalid_input_cleanly():
    client = TestClient(app)
    for path in ("/v1/geometry/step", "/v1/cv/measure", "/v1/import/preview"):
        response = client.post(path, files={"file": ("invalid.txt", b"not a valid engineering upload")})
        assert response.status_code not in (500, 502), (path, response.text)
