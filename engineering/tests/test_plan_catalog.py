from app.plan_catalog import FEATURE_MINIMUM_PLANS, PLAN_LIMITS, feature_allowed


def test_plan_limits_match_customer_contract():
    assert PLAN_LIMITS["free"]["llm_runs_month"] == 10
    assert PLAN_LIMITS["hobbyist"]["llm_runs_month"] == 100
    assert PLAN_LIMITS["startup"]["llm_runs_month"] == 1000
    assert PLAN_LIMITS["enterprise"]["llm_runs_month"] == -1


def test_capabilities_are_monotonic_by_tier():
    order = ("free", "hobbyist", "startup", "enterprise")
    for feature, minimum in FEATURE_MINIMUM_PLANS.items():
        minimum_index = order.index(minimum)
        for index, plan in enumerate(order):
            assert feature_allowed(plan, feature) is (index >= minimum_index)


def test_unknown_capabilities_fail_closed():
    assert feature_allowed("free", "invented_capability") is False
    assert feature_allowed("enterprise", "invented_capability") is False
    assert feature_allowed("unknown_plan", "requirements") is False
