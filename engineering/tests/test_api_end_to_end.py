from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_predict_to_acceptance_to_experiment():
    r=client.post('/v1/predict',json={'nominal_mm':40,'material':'PETG','machine':'X1C','process_temperature_c':245,'nominal_shrinkage_pct':.4,'shrinkage_uncertainty_pct':.1,'tolerance_lower_mm':-.2,'tolerance_upper_mm':.2})
    assert r.status_code==200
    p=r.json(); assert p['status']=='not_calibrated'
    a=client.post('/v1/acceptance',json={'nominal_mm':40,'lower_tol_mm':-.2,'upper_tol_mm':.2,'observed_sigma_mm':.02,'measurement_sigma_mm':.01,'n_observations':10})
    assert a.status_code==200
    e=client.post('/v1/next-experiment',json={'features':[{'name':'width','uncertainty_mm':.08},{'name':'height','uncertainty_mm':.02}]})
    assert e.status_code==200 and e.json()['experiment']['target']['name']=='width'

def test_import_requires_confirmation():
    r=client.post('/v1/import/preview',files={'file':('inspection.csv',b'Serial,Measured,Nominal\nA1,39.9,40\n','text/csv')})
    assert r.status_code==200 and r.json()['requires_confirmation'] is True

def test_step_is_honest_about_units():
    step=b"ISO-10303-21;DATA;#10=CARTESIAN_POINT('',(0.,0.,0.));#11=CARTESIAN_POINT('',(40.,20.,10.));ENDSEC;END-ISO-10303-21;"
    r=client.post('/v1/geometry/step',files={'file':('part.step',step,'application/octet-stream')})
    assert r.status_code==200 and r.json()['feature_extraction']['status']=='limited'
