from datetime import datetime,timedelta,timezone
from app.machine_health import AnalysisRequest,Observation,analyze
def o(i,c=.05):
 return Observation(machine_id="M1",observed_at=datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(days=i),correction_mm=c,correction_direction=1,ambient_temperature_c=23,ambient_rh_pct=35,dew_point_c=7,atmospheric_pressure_kpa=101.3,filament_rh_pct=12,nozzle_hours=i,pressure_advance=.04,resonance_x_hz=52,resonance_y_hz=49,vibration_amplitude=.2,reference_artifact=True)
def test_requires_baseline():
 r=analyze(AnalysisRequest(observations=[o(i) for i in range(10)]));assert r["status"]=="baseline_required"
def test_detects_shift():
 r=analyze(AnalysisRequest(observations=[o(i) for i in range(30)]+[o(30,.25)]));assert any(x["type"]=="correction_residual_shift" for x in r["signals"])
def test_nonlinear_gate():
 r=analyze(AnalysisRequest(observations=[o(i) for i in range(100)]));assert r["nonlinear_model_allowed"] is True
