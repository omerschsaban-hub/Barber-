import numpy as np

from app.quality import QualityRequest, quality_review, enhanced_package, enhanced_guide
from services.engine.sim2real_policy import auto_fix, TARGET_MAPE_PERCENT


def test_quality_review_has_ten_explicit_gates_and_blocks_missing_physical_evidence():
    result = quality_review(QualityRequest())
    assert len(result["gates"]) == 10
    assert result["status"] == "blocked"
    assert result["blocked_gates"] >= 1


def test_package_contains_real_evidence_artifacts():
    package = enhanced_package(QualityRequest(project_name="test", revision="r1", material="PETG", machine="FDM"))
    names = {x["name"] for x in package["contents"]}
    assert "cv_evidence/" in names
    assert "sim2real_calibration.json" in names
    assert "release_manifest.json" in names


def test_build_guide_is_ten_step_and_evidence_gated():
    guide = enhanced_guide(QualityRequest())
    assert len(guide["steps"]) == 10
    assert "Never claim 98% accuracy without held-out real evidence." in guide["guide_markdown"]


def test_sim2real_scores_on_held_out_data():
    predicted = np.linspace(100, 109, 20)
    measured = predicted * 1.001
    fit, history, target = auto_fix(predicted, measured)
    assert history
    assert fit.mape <= TARGET_MAPE_PERCENT
    assert target is True


def test_sim2real_does_not_hide_large_real_error():
    predicted = np.linspace(100, 109, 20)
    measured = predicted * 1.08
    fit, history, target = auto_fix(predicted, measured)
    assert history
    assert fit.mape > TARGET_MAPE_PERCENT or target is False
