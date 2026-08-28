from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

from .owned_auth import _bearer, user_from_token
from .plan_catalog import FEATURE_MINIMUM_PLANS, PLAN_LIMITS, access_for_user, feature_allowed

router = APIRouter(prefix="/v1/plans", tags=["plans"])

# Explicitly enumerate the capabilities promised by the web plan registry. Unknown
# names are not silently treated as Free; they must be added here before release.
FEATURES = FEATURE_MINIMUM_PLANS

IMPLEMENTATION = {
    "available": {"requirements", "basic_mcp", "check", "prove", "inspect", "history", "evidence", "digital_thread",
                   "fix", "build", "bom", "firmware_readiness", "test_plan", "supplier_readiness", "release", "automate",
                   "advanced_sim2real", "production_monitoring", "personal_mcp", "larger_storage", "unlimited_projects",
                   "team", "shared_workspace", "team_roles", "project_permissions", "approval_gates", "team_audit_log",
                   "shared_evidence", "team_automation", "api_access", "webhooks", "organization_billing", "seat_management",
                   "governance", "usage_quotas", "spend_controls", "retention_controls", "service_accounts"},
    "configured_integration": {"github_integration", "notifications", "team_dashboards", "priority_processing", "saml_sso", "scim",
                                "custom_integrations", "private_deployment", "dedicated_infrastructure", "procurement_workflows",
                                "compliance_reports", "sla", "priority_incident_response", "mcp_governance", "security_policies",
                                "ip_allowlist", "session_controls", "custom_roles", "org_hierarchy", "workspace_isolation"},
}


def capability_status(feature: str) -> str:
    for status, names in IMPLEMENTATION.items():
        if feature in names:
            return status
    return "not_implemented"


@router.get("/capabilities")
def capabilities(request: Request, authorization: str | None = Header(default=None)):
    identity = user_from_token(_bearer(request, authorization))
    if not identity:
        raise HTTPException(401, "Authentication required")
    access = access_for_user(identity["user_id"])
    plan = access["plan"]
    return {
        "plan": plan,
        "limits": PLAN_LIMITS[plan],
        "capabilities": [
            {"feature": feature, "minimum_plan": minimum, "allowed": feature_allowed(plan, feature), "status": capability_status(feature)}
            for feature, minimum in FEATURES.items()
        ],
    }
