from pytest import approx

from services.engine.app import CalibrationObservation, EngineeringInput, baseline, fit


def test_baseline_deterministic():
    x = EngineeringInput(nominal_mm=40, material="PETG", machine="X1C")
    assert baseline(x) == baseline(x)


def test_fit_returns_metrics_for_small_observation_sets():
    mean, std, mae, mape = fit([CalibrationObservation(predicted_mm=40, measured_mm=40.1)])
    assert mean == approx(0.1)
    assert std == 0
    assert mae == approx(0.1)
    assert mape == approx(100 * 0.1 / 40.1)


def test_fit_metrics_scale_with_observation_count():
    observations = [CalibrationObservation(predicted_mm=40, measured_mm=40.1) for _ in range(3)]
    mean, std, mae, mape = fit(observations)
    assert mean == approx(0.1)
    assert std == approx(0)
    assert mae == approx(0.1)
    assert mape == approx(100 * 0.1 / 40.1)

    observations = [CalibrationObservation(predicted_mm=40, measured_mm=40.1) for _ in range(10)]
    assert fit(observations)[0] == approx(0.1)
    assert fit(observations)[2] == approx(0.1)
