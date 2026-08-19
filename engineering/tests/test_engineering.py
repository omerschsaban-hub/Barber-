from app.main import physics,EngineeringInput

def test_physics_is_deterministic():
    x=EngineeringInput(nominal_mm=40,material='PETG',machine='M1',process_temperature_c=245,nominal_shrinkage_pct=.5,shrinkage_uncertainty_pct=.1)
    a=physics(x);b=physics(x);assert a==b;assert round(a[0],3)==39.8

def test_uncertainty_is_nonzero():
    x=EngineeringInput(nominal_mm=20,material='PLA',machine='M1',process_temperature_c=210,nominal_shrinkage_pct=.3,shrinkage_uncertainty_pct=.2)
    assert physics(x)[1]>0
