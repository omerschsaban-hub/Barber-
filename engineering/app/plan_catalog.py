from __future__ import annotations

import os
from typing import Any

from .postgres import fetch_all, transaction

PLAN_ORDER = ("free", "hobbyist", "startup", "enterprise")
LEGACY_PRO_ENTITLEMENT = "create_an_app_called_fabrinat_pro"
PLAN_LIMITS: dict[str, dict[str, int | float]] = {
    "free": {"llm_runs_month": 10, "projects": 1, "storage_gb": 0.25},
    "hobbyist": {"llm_runs_month": 100, "projects": -1, "storage_gb": 10},
    "startup": {"llm_runs_month": 1000, "projects": -1, "storage_gb": 100},
    "enterprise": {"llm_runs_month": -1, "projects": -1, "storage_gb": -1},
}

# These defaults make the migration backward-compatible. Operators can replace
# them with the exact provider entitlement IDs without changing application code.
DEFAULT_ENTITLEMENTS = {
    "hobbyist": ("fabrinat_hobby", LEGACY_PRO_ENTITLEMENT),
    "startup": ("fabrinat_startup",),
    "enterprise": ("fabrinat_enterprise",),
}
DEFAULT_PRODUCTS = {
    "hobbyist": ("hobby_monthly",),
    "startup": ("startup_monthly", "startup_monthly_v2"),
}


def _csv(name: str) -> set[str]:
    return {item.strip() for item in os.getenv(name, "").split(",") if item.strip()}


def _configured_entitlements(plan: str) -> set[str]:
    values = set(DEFAULT_ENTITLEMENTS.get(plan, ()))
    values.update(_csv(f"FABRIENT_{plan.upper()}_ENTITLEMENTS"))
    return values


def _configured_products(plan: str) -> set[str]:
    values = set(DEFAULT_PRODUCTS.get(plan, ()))
    values.update(_csv(f"FABRIENT_{plan.upper()}_PRODUCT_IDS"))
    return values


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


FEATURE_MINIMUM_PLANS = {
    "requirements": "free", "basic_mcp": "free", "check": "free", "prove": "free", "inspect": "free",
    "history": "free", "evidence": "free", "digital_thread": "free",
    "fix": "hobbyist", "build": "hobbyist", "bom": "hobbyist", "firmware_readiness": "hobbyist",
    "test_plan": "hobbyist", "supplier_readiness": "hobbyist", "release": "hobbyist", "automate": "hobbyist",
    "advanced_sim2real": "hobbyist", "production_monitoring": "hobbyist", "personal_mcp": "hobbyist",
    "larger_storage": "hobbyist", "unlimited_projects": "hobbyist",
    "team": "startup", "shared_workspace": "startup", "team_roles": "startup", "project_permissions": "startup",
    "approval_gates": "startup", "team_audit_log": "startup", "shared_evidence": "startup", "team_automation": "startup",
    "api_access": "startup", "webhooks": "startup", "github_integration": "startup", "notifications": "startup",
    "team_dashboards": "startup", "usage_controls": "startup", "organization_billing": "startup", "seat_management": "startup",
    "priority_processing": "startup",
    "governance": "enterprise", "saml_sso": "enterprise", "scim": "enterprise", "custom_roles": "enterprise",
    "org_hierarchy": "enterprise", "workspace_isolation": "enterprise", "security_policies": "enterprise", "ip_allowlist": "enterprise",
    "session_controls": "enterprise", "service_accounts": "enterprise", "mcp_governance": "enterprise", "usage_quotas": "enterprise",
    "spend_controls": "enterprise", "retention_controls": "enterprise", "compliance_reports": "enterprise", "sla": "enterprise",
    "priority_incident_response": "enterprise", "custom_integrations": "enterprise", "private_deployment": "enterprise",
    "dedicated_infrastructure": "enterprise", "procurement_workflows": "enterprise",
}


def feature_allowed(plan: str, feature: str) -> bool:
    minimum = FEATURE_MINIMUM_PLANS.get(feature)
    if minimum is None or plan not in PLAN_ORDER:
        return False
    return PLAN_ORDER.index(plan) >= PLAN_ORDER.index(minimum)


def load_plan_mapping_for_debug() -> dict[str, Any]:
    return {
        "entitlements": {plan: sorted(_configured_entitlements(plan)) for plan in DEFAULT_ENTITLEMENTS},
        "products": {plan: sorted(_configured_products(plan)) for plan in PLAN_ORDER[1:]},
        "limits": PLAN_LIMITS,
    }
