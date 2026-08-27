from __future__ import annotations

import os
from typing import Any

from .postgres import fetch_all, transaction

PLAN_ORDER = ("free", "hobbyist", "startup", "enterprise")
LEGACY_PRO_ENTITLEMENT = "create_an_app_called_fabrinat_pro"
PLAN_LIMITS: dict[str, dict[str, int | float]] = {
    "free": {"llm_runs_month": 0, "projects": 1, "storage_gb": 0.25},
    "hobbyist": {"llm_runs_month": 100, "projects": -1, "storage_gb": 10},
    "startup": {"llm_runs_month": 1000, "projects": -1, "storage_gb": 100},
    "enterprise": {"llm_runs_month": -1, "projects": -1, "storage_gb": -1},
}

# These defaults make the migration backward-compatible. Operators can replace
# them with the exact RevenueCat entitlement IDs without changing application code.
DEFAULT_ENTITLEMENTS = {
    "hobbyist": ("fabrinat_hobby", LEGACY_PRO_ENTITLEMENT),
    "startup": ("fabrinat_startup",),
    "enterprise": ("fabrinat_enterprise",),
}


def _csv(name: str) -> set[str]:
    return {item.strip() for item in os.getenv(name, "").split(",") if item.strip()}


def _configured_entitlements(plan: str) -> set[str]:
    values = set(DEFAULT_ENTITLEMENTS.get(plan, ()))
    values.update(_csv(f"FABRIENT_{plan.upper()}_ENTITLEMENTS"))
    return values


def _configured_products(plan: str) -> set[str]:
    return _csv(f"FABRIENT_{plan.upper()}_PRODUCT_IDS")


def active_entitlements(user_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """select entitlement_id, product_id, expires_at from billing_entitlements
           where user_id=%s and active=true and (expires_at is null or expires_at>now())""",
        (user_id,),
    )


def resolve_plan(rows: list[dict[str, Any]]) -> str:
    for plan in reversed(PLAN_ORDER[1:]):
        entitlement_ids = _configured_entitlements(plan)
        product_ids = _configured_products(plan)
        if any(row.get("entitlement_id") in entitlement_ids or row.get("product_id") in product_ids for row in rows):
            return plan
    return "free"


def access_for_user(user_id: str) -> dict[str, Any]:
    rows = active_entitlements(user_id)
    plan = resolve_plan(rows)
    return {
        "plan": plan,
        "limits": PLAN_LIMITS[plan],
        "entitlements": [row.get("entitlement_id") for row in rows],
        "products": [row.get("product_id") for row in rows if row.get("product_id")],
        "legacy_pro": LEGACY_PRO_ENTITLEMENT in {row.get("entitlement_id") for row in rows},
    }


def consume_llm_run(user_id: str) -> dict[str, Any]:
    access = access_for_user(user_id)
    limit = int(access['limits']['llm_runs_month'])
    with transaction() as conn:
        row = conn.execute(
            """insert into plan_usage_monthly(user_id, period_start, llm_runs)
               values(%s, date_trunc('month', now())::date, 1)
               on conflict(user_id, period_start) do update
               set llm_runs = plan_usage_monthly.llm_runs + 1, updated_at = now()
               where plan_usage_monthly.llm_runs < %s or %s < 0
               returning llm_runs""",
            (user_id, limit, limit),
        ).fetchone()
    if not row:
        return {'allowed': False, 'plan': access['plan'], 'limit': limit, 'remaining': 0}
    return {'allowed': True, 'plan': access['plan'], 'limit': limit, 'remaining': -1 if limit < 0 else max(limit - int(row['llm_runs']), 0)}


def feature_allowed(plan: str, feature: str) -> bool:
    minimum = {
        "fix": "hobbyist", "build": "hobbyist", "bom": "hobbyist", "automate": "hobbyist",
        "advanced_sim2real": "hobbyist", "production_monitoring": "hobbyist",
        "team": "startup", "shared_workspace": "startup", "api_access": "startup",
        "governance": "enterprise", "saml_sso": "enterprise", "private_deployment": "enterprise",
    }.get(feature, "free")
    return PLAN_ORDER.index(plan) >= PLAN_ORDER.index(minimum)


def load_plan_mapping_for_debug() -> dict[str, Any]:
    return {
        "entitlements": {plan: sorted(_configured_entitlements(plan)) for plan in DEFAULT_ENTITLEMENTS},
        "products": {plan: sorted(_configured_products(plan)) for plan in PLAN_ORDER[1:]},
        "limits": PLAN_LIMITS,
    }
