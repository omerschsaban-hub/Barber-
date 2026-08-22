export type FabrinatPlan = 'free' | 'hobbyist' | 'startup' | 'enterprise';

export type FabrinatFeature =
  | 'requirements' | 'check' | 'fix' | 'prove' | 'build' | 'inspect' | 'history'
  | 'bom' | 'firmware_readiness' | 'test_plan' | 'supplier_readiness' | 'release'
  | 'automate' | 'evidence' | 'team' | 'advanced_sim2real' | 'production_monitoring'
  | 'digital_thread' | 'api_access' | 'governance';

export const FABRINAT_PLANS = {
  free: {
    name: 'Free', audience: 'Anyone getting started',
    tagline: 'A genuinely useful engineering workspace.',
    features: ['requirements','check','prove','inspect','history','basic_mcp','digital_thread'],
  },
  hobbyist: {
    name: 'Hobbyist', audience: 'One builder',
    tagline: 'Your personal product-building system.',
    features: ['requirements','check','fix','prove','build','inspect','history','bom','firmware_readiness','test_plan','supplier_readiness','release','automate','evidence','advanced_sim2real','production_monitoring','digital_thread','personal_mcp','larger_storage','unlimited_projects'],
  },
  startup: {
    name: 'Startup', audience: 'Teams under 30 people',
    tagline: 'Design, build and ship together without the coordination mess.',
    features: ['all_hobbyist','shared_workspace','team_roles','project_permissions','approval_gates','team_audit_log','shared_evidence','team_automation','api_access','webhooks','github_integration','notifications','team_dashboards','usage_controls','organization_billing','seat_management','priority_processing'],
  },
  enterprise: {
    name: 'Enterprise', audience: 'Organizations with 30+ people',
    tagline: 'The product engineering control layer at scale.',
    features: ['all_startup','saml_sso','scim','custom_roles','org_hierarchy','workspace_isolation','security_policies','ip_allowlist','session_controls','service_accounts','mcp_governance','usage_quotas','spend_controls','retention_controls','compliance_reports','sla','priority_incident_response','custom_integrations','private_deployment','dedicated_infrastructure','procurement_workflows'],
  },
} as const;

export const PRODUCT_LOOP = [
  { key: 'requirements', title: 'Define', description: 'Turn the idea into clear requirements and acceptance criteria.' },
  { key: 'check', title: 'Check', description: 'Find fit, geometry, DFM and manufacturing problems early.' },
  { key: 'fix', title: 'Fix', description: 'Propose changes and verify that fixes actually worked.' },
  { key: 'prove', title: 'Prove', description: 'Keep the evidence behind every important engineering decision.' },
  { key: 'build', title: 'Build', description: 'Create the files, instructions and checks needed to make it.' },
  { key: 'inspect', title: 'Inspect', description: 'Compare real measurements with the acceptance criteria.' },
  { key: 'history', title: 'Learn', description: 'Carry real-world results back into the next revision.' },
] as const;

export const FEATURE_COPY: Record<string, { title: string; description: string; minimumPlan: FabrinatPlan }> = {
  requirements: { title: 'Requirements', description: 'Keep what the product must do next to the evidence that proves it.', minimumPlan: 'free' },
  check: { title: 'Check', description: 'Find manufacturing and fit problems before they cost time or parts.', minimumPlan: 'free' },
  fix: { title: 'Fix', description: 'Turn a finding into a proposed change and verify the result.', minimumPlan: 'hobbyist' },
  prove: { title: 'Prove', description: 'See the measurements and checks behind important decisions.', minimumPlan: 'free' },
  build: { title: 'Build', description: 'Prepare the manufacturing package and physical build instructions.', minimumPlan: 'hobbyist' },
  inspect: { title: 'Inspect', description: 'Turn real measurements into a simple pass, review or fail decision.', minimumPlan: 'free' },
  history: { title: 'Learn', description: 'See what changed and feed real build results into the next revision.', minimumPlan: 'free' },
  bom: { title: 'Parts', description: 'Track the components and materials needed to make the product.', minimumPlan: 'hobbyist' },
  firmware_readiness: { title: 'Firmware', description: 'Track hardware/firmware dependencies before a build is released.', minimumPlan: 'hobbyist' },
  test_plan: { title: 'Test plan', description: 'Turn requirements into repeatable physical and digital acceptance tests.', minimumPlan: 'hobbyist' },
  supplier_readiness: { title: 'Suppliers', description: 'Make sure purchased parts and manufacturing inputs are ready.', minimumPlan: 'hobbyist' },
  release: { title: 'Release', description: 'Create a single controlled handoff from engineering to manufacturing.', minimumPlan: 'hobbyist' },
  automate: { title: 'Automate', description: 'Rerun checks, reports and release gates when the product changes.', minimumPlan: 'hobbyist' },
  team: { title: 'Team', description: 'Share projects, approvals and evidence.', minimumPlan: 'startup' },
  advanced_sim2real: { title: 'Sim → real', description: 'Use validated physical observations to improve bounded predictions.', minimumPlan: 'hobbyist' },
  production_monitoring: { title: 'Production', description: 'Watch drift and quality after the product leaves the design desk.', minimumPlan: 'hobbyist' },
  digital_thread: { title: 'Product thread', description: 'Keep requirements, design, tests, manufacturing and real-world results connected.', minimumPlan: 'free' },
  governance: { title: 'Governance', description: 'Control access, approvals, retention and integrations at organization scale.', minimumPlan: 'enterprise' },
};

export function planHasFeature(plan: FabrinatPlan, feature: string) {
  const order: FabrinatPlan[] = ['free', 'hobbyist', 'startup', 'enterprise'];
  const minimum = FEATURE_COPY[feature]?.minimumPlan;
  if (minimum) return order.indexOf(plan) >= order.indexOf(minimum);
  const features = FABRINAT_PLANS[plan].features as readonly string[];
  return features.includes(feature) || features.includes('all_' + plan);
}

export const ENTERPRISE_CONTACT = { email: 'omerschsaban@gmail.com', phone: '0509220082' };
