from app import EngineeringInput, CalibrationObservation, baseline, fit
def test_baseline_deterministic():
 x=EngineeringInput(nominal_mm=40,material='PETG',machine='X1C'); assert baseline(x)==baseline(x)
def test_no_calibration_without_three_real_observations():
 assert fit([CalibrationObservation(predicted_mm=40,measured_mm=40.1)])[2]=='not_calibrated'
def test_limited_and_validated_thresholds():
 assert fit([CalibrationObservation(predicted_mm=40,measured_mm=40.1) for _ in range(3)])[2]=='limited'
 assert fit([CalibrationObservation(predicted_mm=40,measured_mm=40.1) for _ in range(10)])[2]=='validated'
