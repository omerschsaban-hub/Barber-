import numpy as np
from fastapi.testclient import TestClient

from app.composed import app

client = TestClient(app)


def test_real_cv_measurement_uses_explicit_physical_reference():
    image = np.zeros((200, 300), dtype=np.uint8)
    import cv2
    ok, encoded = cv2.imencode('.png', image)
    assert ok
    response = client.post(
        '/v1/cv/measure-real',
        files={'file': ('test.png', encoded.tobytes(), 'image/png')},
        data={
            'reference_length_mm': '10',
            'reference_line': '[[10,10],[110,10]]',
            'target_line': '[[20,50],[70,50]]',
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'measured'
    assert abs(body['measurement_mm'] - 5.0) < 1e-9
    assert body['provenance']['ground_truth_mm'] is False


def test_sim2real_requires_real_data_before_ml_claim():
    payload = {
        'nominal_mm': 100,
        'shrinkage_pct': 0.5,
        'shrinkage_sigma_pct': 0.1,
        'temperature_c': 200,
        'temperature_sigma_c': 5,
        'n': 300,
        'seed': 7,
    }
    response = client.post('/v1/sim2real/run', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'physics_only'
    assert body['sim_to_real']['real_observations'] == 0
    assert body['sim_to_real']['residual_coupling'] == 'physics_only'


def test_sim2real_calibrates_from_real_observations_only():
    observations = []
    for i in range(10):
        predicted = 100 - i * 0.1
        measured = predicted + 0.02 + 0.001 * i
        observations.append({
            'predicted_mm': predicted,
            'measured_mm': measured,
            'layer_height_mm': 0.2,
            'print_speed_mm_s': 50 + i,
            'nozzle_temp_c': 200,
            'ambient_temp_c': 23,
            'humidity_pct': 50,
            'axis': 0,
        })
    payload = {
        'nominal_mm': 100,
        'shrinkage_pct': 0.5,
        'shrinkage_sigma_pct': 0.1,
        'temperature_c': 200,
        'temperature_sigma_c': 5,
        'observations': observations,
        'n': 300,
        'seed': 11,
    }
    response = client.post('/v1/sim2real/run', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'real_calibrated'
    assert body['sim_to_real']['model']['n_real'] == 10
    assert body['sim_to_real']['model']['held_out_mae_mm'] >= 0
    assert body['sim_to_real']['residual_coupling'] == 'validated_real_residual_model'


def test_agent_fleet_is_bounded_and_critic_blocks_without_real_data():
    response = client.post('/v1/agents/fleet', json={
        'project_id': 'test',
        'objective': 'calibrate an enclosure dimension',
        'max_iterations': 2,
    })
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'blocked'
    assert len(body['agents']) == 9
    assert body['provenance']['synthetic_data_used_for_ml_training'] is False
    assert body['artifacts']['critic']['status'] == 'blocked'
