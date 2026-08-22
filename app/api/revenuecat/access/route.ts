import { NextResponse } from 'next/server'

const PROJECT_ID = 'projb138a8db'
const PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'

const FREE_FEATURES = [
  'overview',
  'project_tracking',
  'basic_dfm_summary',
  'release_status',
] as const

const PRO_FEATURES = [
  'advanced_3d_risk_analysis',
  'manufacturing_package_export',
  'advanced_inspection_analytics',
  'extended_mcp_tools',
] as const

export async function GET(request: Request) {
  const authorization = request.headers.get('authorization')
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const revenueCatSecret = process.env.REVENUECAT_SECRET_API_KEY

  if (!authorization?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  if (!supabaseUrl || !supabaseAnonKey || !revenueCatSecret) {
    return NextResponse.json({ error: 'Billing access is not configured' }, { status: 503 })
  }

  try {
    const userResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: {
        apikey: supabaseAnonKey,
        Authorization: authorization,
      },
      cache: 'no-store',
    })

    if (!userResponse.ok) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    const user = await userResponse.json() as { id?: string }
    if (!user.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

    const customerResponse = await fetch(
      `https://api.revenuecat.com/v2/projects/${PROJECT_ID}/customers/${encodeURIComponent(user.id)}/active_entitlements`,
      {
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${revenueCatSecret}`,
        },
        cache: 'no-store',
      },
    )

    if (!customerResponse.ok) {
      return NextResponse.json({ error: 'Unable to verify subscription' }, { status: 502 })
    }

    const customer = await customerResponse.json() as { items?: Array<{ entitlement?: { lookup_key?: string } }> }
    const pro = (customer.items ?? []).some(item => item.entitlement?.lookup_key === PRO_ENTITLEMENT)

    return NextResponse.json({
      authenticated: true,
      pro,
      availableFeatures: pro ? [...FREE_FEATURES, ...PRO_FEATURES] : [...FREE_FEATURES],
      gatedFeatures: pro ? [] : [...PRO_FEATURES],
      entitlement: PRO_ENTITLEMENT,
    })
  } catch (error) {
    console.error('[RevenueCat] access check failed', error)
    return NextResponse.json({ error: 'Unable to verify subscription' }, { status: 502 })
  }
}
