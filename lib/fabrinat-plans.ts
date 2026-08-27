export type FabrinatPlan = 'free' | 'hobbyist' | 'startup' | 'enterprise';

export type FabrinatFeature =
  | 'requirements' | 'check' | 'fix' | 'prove' | 'build' | 'inspect' | 'history'
  | 'bom' | 'firmware_readiness' | 'test_plan' | 'supplier_readiness' | 'release'
  | 'automate' | 'evidence' | 'team' | 'advanced_sim2real' | 'production_monitoring'
  | 'digital_thread' | 'api_access' | 'governance';

export const FABRINAT_PLANS = {
  free: {
    name: 'Free', audience: 'Anyone getting started', price: 0, billingLabel: 'Always free', teamSize: '1 person',
    tagline: 'A genuinely useful engineering workspace.',
    limits: { llmRuns: 10, projects: 1, storageGb: 0.25 },
    highlights: ['Core Define → Check → Prove loop', '10 guided AI runs each month', '1 project · 250 MB evidence storage'],
    features: ['requirements','check','prove','inspect','history','basic_mcp','digital_thread'],
  },
  hobbyist: {
    name: 'Hobby', audience: 'One builder', price: 9, billingLabel: '$9 / month', teamSize: '1 person',
    tagline: 'Your personal product-building system.',
    limits: { llmRuns: 100, projects: -1, storageGb: 10 },
    highlights: ['Every individual engineering feature', '100 AI-assisted runs each month', 'Unlimited personal projects · 10 GB storage'],
    features: ['requirements','check','fix','prove','build','inspect','history','bom','firmware_readiness','test_plan','supplier_readiness','release','automate','evidence','advanced_sim2real','production_monitoring','digital_thread','personal_mcp','larger_storage','unlimited_projects'],
  },
  startup: {
    name: 'Startup', audience: 'Teams of 1–29 people', price: 49, billingLabel: '$49 / month', teamSize: '1–29 people',
    tagline: 'Design, build and ship together without the coordination mess.',
    limits: { llmRuns: 1000, projects: -1, storageGb: 100 },
    highlights: ['Everything in Hobby for the whole team', '1,000 AI-assisted runs each month', 'Roles, approvals, API, webhooks and dashboards'],
    features: ['all_hobbyist','shared_workspace','team_roles','project_permissions','approval_gates','team_audit_log','shared_evidence','team_automation','api_access','webhooks','github_integration','notifications','team_dashboards','usage_controls','organization_billing','seat_management','priority_processing'],
  },
  enterprise: {
    name: 'Enterprise', audience: 'Organizations with 30+ people', price: null, billingLabel: 'Let’s talk', teamSize: '30+ people',
    tagline: 'The product engineering control layer at scale.',
    limits: { llmRuns: -1, projects: -1, storageGb: -1 },
    highlights: ['Everything in Startup with organization-wide control', 'Unlimited AI runs with spend and usage controls', 'SSO, SCIM, private deployment, compliance and SLA'],
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
  evidence: { title: 'Evidence', description: 'Keep measurements, provenance and decisions attached to the job.', minimumPlan: 'free' },
  team: { title: 'Team', description: 'Share projects, approvals and evidence.', minimumPlan: 'startup' },
  advanced_sim2real: { title: 'Sim → real', description: 'Use validated physical observations to improve bounded predictions.', minimumPlan: 'hobbyist' },
  production_monitoring: { title: 'Production', description: 'Watch drift and quality after the product leaves the design desk.', minimumPlan: 'hobbyist' },
  digital_thread: { title: 'Product thread', description: 'Keep requirements, design, tests, manufacturing and real-world results connected.', minimumPlan: 'free' },
  api_access: { title: 'API access', description: 'Connect your authenticated engineering workflows to the same capabilities.', minimumPlan: 'startup' },
  governance: { title: 'Governance', description: 'Control access, approvals, retention and integrations at organization scale.', minimumPlan: 'enterprise' },
};

export const PLAN_COMPARISON_ROWS = [
  { feature: 'requirements', label: 'Requirements and acceptance criteria' },
  { feature: 'check', label: 'Deterministic checks and DFM' },
  { feature: 'prove', label: 'Evidence and provenance' },
  { feature: 'inspect', label: 'Inspection records' },
  { feature: 'history', label: 'Project history' },
  { feature: 'fix', label: 'Bounded fixes and reverification' },
  { feature: 'build', label: 'Build and manufacturing package' },
  { feature: 'advanced_sim2real', label: 'Advanced sim → real validation' },
  { feature: 'automate', label: 'Workflow automation' },
  { feature: 'team', label: 'Shared workspace and approvals' },
  { feature: 'api_access', label: 'API and webhooks' },
  { feature: 'governance', label: 'SSO, governance and private deployment' },
] as const;

export function planUsageLabel(plan: FabrinatPlan) {
  const runs = FABRINAT_PLANS[plan].limits.llmRuns;
  return runs === -1 ? 'Unlimited AI runs' : `${runs.toLocaleString()} AI runs / month`;
}

export function planHasFeature(plan: FabrinatPlan, feature: string) {
  const order: FabrinatPlan[] = ['free', 'hobbyist', 'startup', 'enterprise'];
  const minimum = FEATURE_COPY[feature]?.minimumPlan;
  if (minimum) return order.indexOf(plan) >= order.indexOf(minimum);
  const features = FABRINAT_PLANS[plan].features as readonly string[];
  return features.includes(feature) || features.includes('all_' + plan);
}

export const ENTERPRISE_CONTACT = { email: 'omerschsaban@gmail.com', phone: '0509220082' };
