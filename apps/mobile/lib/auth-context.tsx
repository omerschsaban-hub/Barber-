import { createContext, PropsWithChildren, useContext, useEffect, useMemo, useState } from 'react'
import { currentUser, logout as apiLogout, requestOtp, verifyOtp, type OwnedUser } from '@/lib/api'

type AuthContextValue = { user: OwnedUser | null; loading: boolean; error: string | null; sendOtp: (email: string) => Promise<void>; verify: (email: string, code: string) => Promise<void>; logout: () => Promise<void>; clearError: () => void }
const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<OwnedUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { currentUser().then(r => setUser(r.user)).catch(() => setUser(null)).finally(() => setLoading(false)) }, [])
  const value = useMemo<AuthContextValue>(() => ({
    user, loading, error,
    sendOtp: async email => { setError(null); try { await requestOtp(email) } catch (e) { const m = e instanceof Error ? e.message : 'Could not send the sign-in code.'; setError(m); throw e } },
    verify: async (email, code) => { setError(null); try { const r = await verifyOtp(email, code); setUser(r.user) } catch (e) { const m = e instanceof Error ? e.message : 'That code is invalid or expired.'; setError(m); throw e } },
    logout: async () => { await apiLogout(); setUser(null) },
    clearError: () => setError(null),
  }), [user, loading, error])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('useAuth must be used inside AuthProvider'); return value }
