from app.sim2real_20x import (
    CAPABILITIES,
    Evidence,
    EvidenceKind,
    EvidenceStatus,
    Experiment,
    Sim2RealState,
    choose_next_experiment,
    evaluate_release,
    residuals_from_measurements,
)


def test_twenty_capabilities_are_contracts():
    assert len(CAPABILITIES) == 20
    assert "CV measurement extraction with scale validation" in CAPABILITIES
    assert "interpretable residual/system-identification ML" in CAPABILITIES
    assert "evidence-constrained LLM orchestration" in CAPABILITIES


def test_residuals_use_observations_only():
    residuals = residuals_from_measurements(
        {"width": 10.0}, {"width": 10.4}, {"width": 0.2}
    )
    assert residuals[0].residual == 0.4
    assert residuals[0].normalized == 2.0


def test_next_experiment_uses_information_per_cost_and_risk():
    experiments = [
        Experiment("a", "calibrate", 10, 5, 0.0),
        Experiment("b", "inspect", 8, 2, 0.0),
    ]
    assert choose_next_experiment(experiments).id == "b"


def test_release_refuses_without_physical_evidence():
    state = Sim2RealState(
        residuals=residuals_from_measurements({"x": 1}, {"x": 1.1}),
    )
    result = evaluate_release(state)
    assert result["ready"] is False
    assert "validated physical evidence is required" in result["blockers"]


def test_release_requires_real_evidence_even_when_simulation_exists():
    state = Sim2RealState(
        residuals=residuals_from_measurements({"x": 1}, {"x": 1.1}),
        evidence=[
            Evidence(EvidenceKind.PHYSICS, "x", EvidenceStatus.VALIDATED, 1.0),
        ],
    )
    result = evaluate_release(state)
    assert result["ready"] is False
    assert "validated physical evidence is required" in result["blockers"]
