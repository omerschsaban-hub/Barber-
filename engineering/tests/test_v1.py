from fastapi.testclient import TestClient
from app.composed import app

client = TestClient(app)

def test_health():
    r=client.get('/health'); assert r.status_code==200; assert r.json()['ok'] is True

def test_refuses_too_tight_tolerance():
    r=client.post('/v1/acceptance',json={'nominal_mm':8,'lower_tol_mm':-0.02,'upper_tol_mm':0.02,'observed_sigma_mm':0.03,'measurement_sigma_mm':0.01,'n_observations':20})
    assert r.status_code==200; assert r.json()['status']=='refused'

def test_reverification_requires_real_rate():
    r=client.post('/v1/reverification',json={'tolerance_band_mm':0.4,'uses_per_week':20,'environment_severity':0.2,'observed_drift_mm_per_day':0,'consequence_severity':0.5,'measurement_uncertainty_mm':0.01})
    assert r.json()['status']=='insufficient_data'

def test_import_preview_never_auto_accepts_mapping():
    r=client.post('/v1/import/preview',files={'file':('inspection.csv','Serial,Actual,Nominal\nG1,39.9,40\n','text/csv')})
    assert r.status_code==200; body=r.json(); assert body['requires_confirmation'] is True

def test_agent_graph_is_bounded():
    r=client.post('/v1/agent-graph',json={'project_id':'p','max_iterations':4,'approval_required':True})
    assert r.status_code==200; assert r.json()['bounded'] is True; assert r.json()['max_iterations']==4

def test_residual_model_needs_real_data():
    r=client.post('/v1/residual-uncertainty',json={'physics_sigma_mm':.01,'measurement_sigma_mm':.01,'model_sigma_mm':.01,'residuals_mm':[],'n_real_observations':0})
    assert r.json()['status']=='not_calibrated'
