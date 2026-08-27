import AsyncStorage from '@react-native-async-storage/async-storage'

const API_BASE = (process.env.EXPO_PUBLIC_FABRIENT_API_URL || 'https://fabrient-engineering.onrender.com').replace(/\/$/, '')
const SESSION_KEY = 'fabrient.session.token'

export type OwnedUser = { id: string; email: string; display_name?: string | null; role?: string }
export type AuthResult = { user: OwnedUser; session_token: string; expires_in: number }
export type BillingAccess = { authenticated: boolean; pro: boolean; plan: string; entitlement?: string | null; limits?: Record<string, unknown> }

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 15000): Promise<T> {
  const token = await AsyncStorage.getItem(SESSION_KEY)
  const headers = new Headers(init.headers)
  headers.set('content-type', 'application/json')
  if (token) headers.set('authorization', `Bearer ${token}`)
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal })
    const body = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status})`)
    return body as T
  } finally { clearTimeout(timeout) }
}

export async function requestOtp(email: string) { return request<{ ok: boolean }>('/auth/request-otp', { method: 'POST', body: JSON.stringify({ email: email.trim().toLowerCase() }) }) }
export async function verifyOtp(email: string, code: string) {
  const result = await request<AuthResult>('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ email: email.trim().toLowerCase(), code: code.trim() }) })
  await AsyncStorage.setItem(SESSION_KEY, result.session_token)
  return result
}
export async function currentUser() { return request<{ user: OwnedUser }>('/auth/me') }
export async function logout() { try { await request('/auth/logout', { method: 'POST' }) } finally { await AsyncStorage.removeItem(SESSION_KEY) } }
export async function billingAccess() { return request<BillingAccess>('/billing/access') }
export async function engineeringHealth() { return request<{ ok: boolean; service: string; database_configured?: boolean }>('/health', {}, 20000) }
export async function hasSession() { return Boolean(await AsyncStorage.getItem(SESSION_KEY)) }
export { API_BASE }
