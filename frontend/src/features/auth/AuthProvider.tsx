import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, hasAccessToken, refreshAccessToken, setSessionExpiredHandler } from '@/lib/api'
import type { Role, User } from '@/lib/types'

interface AuthState {
  user: User | null
  status: 'loading' | 'authenticated' | 'anonymous'
  sessionExpired: boolean
  /** True after a deliberate sign-out, so the next person does not land on the previous user's page. */
  signedOut: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  hasRole: (...roles: Role[]) => boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthState['status']>('loading')
  const [sessionExpired, setSessionExpired] = useState(false)
  const [signedOut, setSignedOut] = useState(false)

  // On load, try the HttpOnly refresh cookie to restore an existing session.
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const ok = hasAccessToken() || (await refreshAccessToken())
      if (cancelled) return
      if (!ok) return setStatus('anonymous')
      try {
        const me = await api.me()
        if (!cancelled) {
          setUser(me)
          setStatus('authenticated')
        }
      } catch {
        if (!cancelled) setStatus('anonymous')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null)
      setStatus('anonymous')
      setSessionExpired(true)
      queryClient.clear()
    })
    return () => setSessionExpiredHandler(null)
  }, [queryClient])

  const signIn = useCallback(async (email: string, password: string) => {
    await api.login(email, password)
    const me = await api.me()
    setSessionExpired(false)
    setSignedOut(false)
    setUser(me)
    setStatus('authenticated')
  }, [])

  const signOut = useCallback(async () => {
    await api.logout()
    queryClient.clear()
    setSignedOut(true)
    setUser(null)
    setStatus('anonymous')
  }, [queryClient])

  const value = useMemo<AuthState>(
    () => ({ user, status, sessionExpired, signedOut, signIn, signOut, hasRole: (...roles) => !!user && roles.includes(user.role) }),
    [user, status, sessionExpired, signedOut, signIn, signOut],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
