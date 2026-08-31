from engineering.app.reality_engine import Observation, active_experiment, autonomous_plan, compare, fit_residual_model

def sample(n=10):
    return [Observation(predicted=10+i*0.01, measured=10+i*0.01+0.2, features=(0.2,50,200,23,50,0), group=f"machine-{i%3}", experiment_id=f"e{i}") for i in range(n)]

def test_compare_reports_real_residual():
    result=compare(sample(3)); assert result["n"]==3; assert result["mae"]>0; assert result["worst"]["residual"]==0.2

def test_residual_model_requires_real_evidence():
    assert fit_residual_model(sample(7))["status"]=="not_ready"

def test_residual_model_uses_held_out_validation():
    result=fit_residual_model(sample(10)); assert result["status"]=="validated"; assert result["held_out_mae"]>=0; assert result["validation"] in {"group_holdout","leave_one_out"}

def test_active_experiment_prefers_information_per_cost():
    result=active_experiment(sample(10),[{"id":"cheap-high-info","sensitivity":[3,3],"noise":1,"cost":1},{"id":"expensive-low-info","sensitivity":[2],"noise":1,"cost":10}]); assert result["experiment"]["id"]=="cheap-high-info"

def test_autonomous_plan_never_claims_validation_without_enough_evidence():
    result=autonomous_plan(sample(7)); assert result["status"]=="loop_open"; assert result["calibration"]["status"]=="not_ready"; assert "real observations only" in result["evidence_policy"]
