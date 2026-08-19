from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.final_pipeline import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_risk_refuses_interval_outside_tolerance():
    r = client.post('/v1/final/risk', json={'nominal_mm':10,'predicted_mm':10.8,'uncertainty_mm':0.2,'lower_tol_mm':-0.2,'upper_tol_mm':0.2})
    assert r.status_code == 200
    assert r.json()['result']['risk_level'] == 'refuse'
    assert r.json()['result']['supported'] is False


def test_import_confirmation_requires_critical_fields():
    r = client.post('/v1/final/import/confirm', json={'filename':'x.csv','content_sha256':'abc','mapping':{'a':'serial'},'rows':[],'unit':'mm'})
    assert r.status_code == 422


def test_import_confirmation_accepts_explicit_mapping():
    r = client.post('/v1/final/import/confirm', json={'filename':'x.csv','content_sha256':'abc','mapping':{'Serial':'serial','Feature':'feature','Actual':'measured_mm'},'rows':[{'Serial':'G1','Feature':'width','Actual':'10.1'}],'unit':'mm'})
    assert r.status_code == 200
    assert r.json()['status'] == 'confirmed'
    assert r.json()['synthetic'] is False


def test_system_identification_requires_real_sample_count():
    r = client.post('/v1/final/system-identification', json={'observations':[]})
    assert r.status_code == 200
    assert r.json()['status'] == 'limited'


def test_agent_is_human_gated():
    r = client.post('/v1/final/agent/step', json={'objective':'select next calibration','approved':False})
    assert r.status_code == 200
    assert r.json()['status'] == 'approval_required'


def test_pdf_record_is_generated_from_explicit_record():
    record={'serial':'G-001','machine':'Printer-1','date':'2026-08-19','acceptance_criteria':'10.0 +/- 0.2 mm','measurements':[{'feature':'width','nominal_mm':10,'measured_mm':10.03,'lower_tol_mm':-0.2,'upper_tol_mm':0.2,'status':'pass'}]}
    r=client.post('/v1/final/inspection-record/pdf',json=record)
    assert r.status_code==200
    assert r.headers['content-type'].startswith('application/pdf')
    assert r.content.startswith(b'%PDF')
