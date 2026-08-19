from fastapi.testclient import TestClient
from app.fabrient_app import app

client = TestClient(app)


def test_complete_api_exposes_health_and_final_risk():
    health = client.get('/health')
    assert health.status_code == 200
    risk = client.post('/v1/final/risk', json={
        'nominal_mm': 20,
        'predicted_mm': 20.02,
        'uncertainty_mm': 0.01,
        'lower_tol_mm': -0.10,
        'upper_tol_mm': 0.10,
    })
    assert risk.status_code == 200
    assert risk.json()['result']['supported'] is True


def test_complete_api_refuses_bad_tolerance():
    r = client.post('/v1/final/risk', json={
        'nominal_mm': 20,
        'predicted_mm': 20,
        'uncertainty_mm': 0.01,
        'lower_tol_mm': 0.10,
        'upper_tol_mm': -0.10,
    })
    assert r.status_code == 422
