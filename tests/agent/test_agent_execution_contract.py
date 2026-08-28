from engineering.app.agent_execution import ACTIONS, DEFAULT_COMPLETION, _next


def test_agent_execution_exposes_small_outcome_focused_action_surface():
    assert list(ACTIONS) == [
        "inspect_job",
        "analyze_design",
        "propose_change",
        "verify_design",
        "submit_physical_evidence",
        "prepare_release",
    ]
    assert ACTIONS["propose_change"]["requires_approval"] is True
    assert ACTIONS["prepare_release"]["requires_approval"] is True
    assert ACTIONS["verify_design"]["requires_approval"] is False


def test_next_action_is_machine_readable_and_bounded():
    job = {"next_action": "propose_change", "blocker": None}
    result = _next(job)
    assert result == {
        "action": "propose_change",
        "kind": "modify",
        "requires_approval": True,
        "reason": None,
        "allowed": True,
    }


def test_completion_contract_is_outcome_based():
    assert "requested outcome produced" in DEFAULT_COMPLETION
    assert "required verification gates passed" in DEFAULT_COMPLETION
    assert "required evidence recorded" in DEFAULT_COMPLETION
