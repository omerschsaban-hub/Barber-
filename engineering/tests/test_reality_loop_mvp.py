from engineering.app.real_cv_sim2real import RealObservation, Sim2RealRequest, sim2real_run
from engineering.app.sim2real_loop import Experiment, RealityLoopRequest, run_reality_loop


def observation(i: int = 0) -> RealObservation:
    return RealObservation(
        predicted_mm=40.0 + i * 0.01,
        measured_mm=40.08 + i * 0.012,
        layer_height_mm=0.2,
        print_speed_mm_s=50 + i,
        nozzle_temp_c=220,
        ambient_temp_c=23,
        humidity_pct=45,
        axis=i % 3,
        machine_id=f"machine-{i % 3}",
        feature_id=f"feature-{i}",
    )


def test_physics_only_has_no_fake_real_calibration():
    result = sim2real_run(Sim2RealRequest(
        nominal_mm=40,
        shrinkage_pct=0.5,
        shrinkage_sigma_pct=0.1,
        temperature_c=220,
        temperature_sigma_c=2,
        observations=[],
    ))
    assert result["status"] == "physics_only"
    assert result["sim_to_real"]["real_observations"] == 0


def test_real_evidence_drives_residual_model_and_held_out_validation():
    observations = [observation(i) for i in range(12)]
    result = sim2real_run(Sim2RealRequest(
        nominal_mm=40,
        shrinkage_pct=0.5,
        shrinkage_sigma_pct=0.1,
        temperature_c=220,
        temperature_sigma_c=2,
        observations=observations,
    ))
    model = result["sim_to_real"]["model"]
    assert model["n_real"] == 12
    assert model["training_source"] == "real_observations_only"
    assert "held_out_mae_mm" in model
    assert result["status"] in {"real_calibrated", "real_informed"}


def test_loop_selects_next_experiment_and_exposes_trust_boundary():
    observations = [observation(i) for i in range(12)]
    candidates = [
        Experiment(name="low-cost", predicted_mm=40, measured_mm=40.09, cost_minutes=5),
        Experiment(name="high-information", predicted_mm=40, measured_mm=40.25, cost_minutes=8),
    ]
    result = run_reality_loop(RealityLoopRequest(
        nominal_mm=40,
        shrinkage_pct=0.5,
        shrinkage_sigma_pct=0.1,
        temperature_c=220,
        temperature_sigma_c=2,
        observations=observations,
        candidate_experiments=candidates,
    ))
    assert result["next_experiment"]["status"] == "selected"
    assert result["next_experiment"]["selected"]["name"] in {"low-cost", "high-information"}
    assert "boundary" in result["trust_envelope"]


def test_loop_never_claims_physical_execution():
    result = run_reality_loop(RealityLoopRequest(
        nominal_mm=40,
        shrinkage_pct=0.5,
        shrinkage_sigma_pct=0.1,
        temperature_c=220,
        temperature_sigma_c=2,
    ))
    assert result["automation"]["physical_execution"].startswith("not automated")
    assert "invent" in result["automation"]["fabrication_policy"]
