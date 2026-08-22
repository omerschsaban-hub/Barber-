export type FabrinatPlan = 'free' | 'hobbyist' | 'startup' | 'enterprise';

export const FABRINAT_PLANS = {
  free: {
    name: 'Free',
    audience: 'Anyone getting started',
    tagline: 'Check your hardware and understand what to fix.',
    features: ['home','check','basic_fix_guidance','build_readiness','basic_inspection','history','why_explanations','basic_mcp'],
  },
  hobbyist: {
    name: 'Hobbyist',
    audience: 'One builder',
    tagline: 'Your personal engineering workspace.',
    features: ['home','check','advanced_checks','fix','automatic_fix_verification','build','full_inspection','history','revision_diff','evidence','engineering_decision_log','sim_to_real','risk_map','manufacturing_package','inspection_templates','measurement_history','calibration_history','automation','scheduled_checks','automatic_reports','personal_mcp','larger_storage','unlimited_projects'],
  },
  startup: {
    name: 'Startup',
    audience: 'Teams under 30 people',
    tagline: 'Ship hardware together without the coordination mess.',
    features: ['all_hobbyist','shared_workspace','team_roles','project_permissions','approval_gates','team_audit_log','shared_evidence','team_automation','api_access','webhooks','github_integration','notifications','team_dashboards','usage_controls','organization_billing','seat_management','priority_processing'],
  },
  enterprise: {
    name: 'Enterprise',
    audience: 'Organizations with 30+ people',
    tagline: 'Engineering control, governance and security at scale.',
    features: ['all_startup','saml_sso','scim','custom_roles','org_hierarchy','workspace_isolation','security_policies','ip_allowlist','session_controls','service_accounts','mcp_governance','usage_quotas','spend_controls','retention_controls','compliance_reports','sla','priority_incident_response','custom_integrations','private_deployment','dedicated_infrastructure','procurement_workflows'],
  },
} as const;

export const FEATURE_COPY: Record<string, { title: string; description: string; minimumPlan: FabrinatPlan }> = {
  check: { title: 'Check', description: 'Find manufacturing problems before they cost you time or parts.', minimumPlan: 'free' },
  fix: { title: 'Fix', description: 'Turn a problem into a proposed change, then verify the result.', minimumPlan: 'hobbyist' },
  build: { title: 'Build', description: 'Prepare the files, requirements and instructions needed to manufacture.', minimumPlan: 'hobbyist' },
  inspect: { title: 'Inspect', description: 'Turn real measurements into a simple pass, review or fail decision.', minimumPlan: 'free' },
  history: { title: 'History', description: 'See what changed between revisions and why it matters.', minimumPlan: 'free' },
  automate: { title: 'Automate', description: 'Let Fabrinat rerun checks and reports when your design changes.', minimumPlan: 'hobbyist' },
  evidence: { title: 'Evidence', description: 'See the measurements and checks behind every important decision.', minimumPlan: 'hobbyist' },
  team: { title: 'Team', description: 'Share projects, approvals and engineering evidence.', minimumPlan: 'startup' },
};

export function planHasFeature(plan: FabrinatPlan, feature: string) {
  const order: FabrinatPlan[] = ['free', 'hobbyist', 'startup', 'enterprise'];
  const featurePlan = Object.entries(FEATURE_COPY).find(([key]) => key === feature)?.[1].minimumPlan;
  if (featurePlan) return order.indexOf(plan) >= order.indexOf(featurePlan);
  const features = FABRINAT_PLANS[plan].features as readonly string[];
  return features.includes(feature) || features.includes('all_' + plan);
}

export const ENTERPRISE_CONTACT = {
  email: 'omerschsaban@gmail.com',
  phone: '0509220082',
};
