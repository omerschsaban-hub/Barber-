import base64

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.composed import app

client = TestClient(app)


def _image_b64():
    image = np.zeros((200, 300), dtype=np.uint8)
    ok, encoded = cv2.imencode('.png', image)
    assert ok
    return base64.b64encode(encoded.tobytes()).decode('ascii')


def test_json_cv_measurement_matches_multipart_contract():
    payload = {
        'image_base64': _image_b64(),
        'reference_length_mm': 10,
        'reference_line': '[[10,10],[110,10]]',
        'target_line': '[[20,50],[70,50]]',
    }
    response = client.post('/v1/cv/measure-real-json', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'measured'
    assert abs(body['measurement_mm'] - 5.0) < 1e-9
    assert body['provenance']['ground_truth_mm'] is False


def test_json_cv_rejects_invalid_base64():
    response = client.post('/v1/cv/measure-real-json', json={
        'image_base64': 'not-base64',
        'reference_length_mm': 10,
        'reference_line': '[[10,10],[110,10]]',
        'target_line': '[[20,50],[70,50]]',
    })
    assert response.status_code == 422


def test_json_cv_line_candidates_are_human_selected():
    response = client.post('/v1/cv/detect-line-candidates-json', json={'image_base64': _image_b64()})
    assert response.status_code == 200
    body = response.json()
    assert body['requires_user_selection'] is True
    assert body['provenance']['ground_truth_mm'] is False
