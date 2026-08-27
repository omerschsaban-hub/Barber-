from services.engine.operation_engine import run_tool_operation


def test_dimension_validation_computes_result():
    result = run_tool_operation("validate_dimension", {"nominal_mm": 10, "measured_mm": 10.04, "tolerance_mm": 0.05})
    assert result["status"] == "pass"
    assert result["deviation_mm"] == 0.03999999999999915


def test_wall_check_fails_when_below_limit():
    result = run_tool_operation("check_wall_thickness", {"wall_thickness_mm": 0.7, "minimum_wall_thickness_mm": 0.8})
    assert result["status"] == "fail"
    assert result["engineering_claims"] is True


def test_data_quality_reports_duplicates_and_missing():
    rows = [{"a": 1, "b": 2}, {"a": 1, "b": 2}, {"a": 2, "b": None}]
    result = run_tool_operation("check_data_quality", {"observations": rows})
    assert result["status"] == "fail"
    assert result["duplicate_rows"] == 1
    assert result["rows_with_missing_values"] == 1


def test_model_requires_real_held_out_evidence():
    rows = [{"features": [1, i], "target": 0.1 + 0.02 * i} for i in range(20)]
    result = run_tool_operation("fit_residual_model", {"observations": rows})
    assert result["status"] == "validated"
    assert result["holdout_observations"] == 10
    assert result["validation"]["held_out"] is True


def test_release_never_auto_releases():
    result = run_tool_operation("manufacturing_release_gate", {"gates": {
        "geometry_verified": True,
        "dfm_passed": True,
        "inspection_plan_ready": True,
        "provenance_complete": True,
        "physical_acceptance": True,
    }})
    assert result["status"] == "ready_for_human_release"
    assert result["released"] is False


def test_agent_operation_is_not_fake_engineering_truth():
    result = run_tool_operation("engineering_agent_run", {})
    assert result["status"] == "pass"
    assert result["engineering_claims"] is False
    assert "evidence_required" in result
