import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError, getToken, setToken } from '../api/client'
import * as api from '../api/endpoints'
import type { MeResult } from '../api/types'

type AuthState = {
  token: string | null
  me: MeResult | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshMe: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTok] = useState<string | null>(() => getToken())
  const [me, setMe] = useState<MeResult | null>(null)
  const [loading, setLoading] = useState(!!getToken())

  const refreshMe = useCallback(async () => {
    const t = getToken()
    if (!t) {
      setMe(null)
      setLoading(false)
      return
    }
    try {
      const m = await api.fetchMe()
      setMe(m)
    } catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
        setToken(null)
        setTok(null)
        setMe(null)
      }
      throw e
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!token) {
      setMe(null)
      setLoading(false)
      return
    }
    setLoading(true)
    refreshMe().catch(() => {
      /* handled in refreshMe */
    })
  }, [token, refreshMe])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password)
    setToken(access_token)
    setTok(access_token)
    setLoading(true)
    await refreshMe()
  }, [refreshMe])

  const logout = useCallback(() => {
    setToken(null)
    setTok(null)
    setMe(null)
  }, [])

  const value = useMemo(
    () => ({ token, me, loading, login, logout, refreshMe }),
    [token, me, loading, login, logout, refreshMe],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/* Hook colocated with provider for this small app */
// eslint-disable-next-line react-refresh/only-export-components -- useAuth is the consumer API for AuthProvider
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
