import base64
import gzip

from fastapi.testclient import TestClient

from app.composed import app
import app.cad_routes as cad_routes


client = TestClient(app)


def test_step_json_base64_upload_reaches_kernel(monkeypatch):
    captured = {}

    def fake_extract_step(path: str):
        captured["bytes"] = open(path, "rb").read()
        return {
            "status": "validated",
            "brep": {"solids": 1, "faces": 6, "edges": 12, "vertices": 8},
            "provenance": {"source": "test-kernel", "synthetic": True},
        }

    monkeypatch.setattr(cad_routes, "extract_step", fake_extract_step)
    raw = b"ISO-10303-21;HEADER;ENDSEC;DATA;ENDSEC;END-ISO-10303-21;"
    response = client.post(
        "/v1/geometry/step",
        json={"filename": "future_smartphone_enclosure.step", "file_base64": base64.b64encode(raw).decode()},
    )
    assert response.status_code == 200
    assert captured["bytes"] == raw
    body = response.json()
    assert body["filename"] == "future_smartphone_enclosure.step"
    assert body["file_size_bytes"] == len(raw)


def test_step_json_gzip_upload_reaches_kernel(monkeypatch):
    captured = {}

    def fake_extract_step(path: str):
        captured["bytes"] = open(path, "rb").read()
        return {"status": "validated", "provenance": {"source": "test-kernel", "synthetic": True}}

    monkeypatch.setattr(cad_routes, "extract_step", fake_extract_step)
    raw = b"ISO-10303-21;HEADER;ENDSEC;DATA;ENDSEC;END-ISO-10303-21;"
    encoded = base64.b64encode(gzip.compress(raw)).decode()
    response = client.post(
        "/v1/geometry/step",
        json={"filename": "model.stp", "file_base64_gzip": encoded},
    )
    assert response.status_code == 200
    assert captured["bytes"] == raw


def test_step_json_rejects_invalid_base64():
    response = client.post(
        "/v1/geometry/step",
        json={"filename": "model.step", "file_base64": "not-base64"},
    )
    assert response.status_code == 422
    assert "valid base64" in response.text


def test_step_json_rejects_invalid_gzip():
    response = client.post(
        "/v1/geometry/step",
        json={"filename": "model.step", "file_base64_gzip": base64.b64encode(b"not-gzip").decode()},
    )
    assert response.status_code == 422
    assert "valid gzip" in response.text


def test_step_json_rejects_missing_file_payload():
    response = client.post(
        "/v1/geometry/step",
        json={"filename": "model.step"},
    )
    assert response.status_code == 422
    assert "file_base64 or file_base64_gzip" in response.text


def test_step_rejects_non_step_filename():
    response = client.post(
        "/v1/geometry/step",
        json={"filename": "model.stl", "file_base64": base64.b64encode(b"data").decode()},
    )
    assert response.status_code == 415
    assert "STEP/STP" in response.text
