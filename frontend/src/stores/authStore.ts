import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, LoginResponse } from '@/types'
import { authApi } from '@/api'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  /** Plain Subsonic password kept only in memory (not persisted). */
  subsonicPassword: string | null
  login: (response: LoginResponse) => void
  logout: () => void
  setUser: (user: User) => void
  setSubsonicCredentials: (password: string | null) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      // Initialise from sessionStorage so that Subsonic continues to work
      // after a page refresh in the same tab, without hitting localStorage.
      subsonicPassword:
        typeof window !== 'undefined'
          ? window.sessionStorage.getItem('subsonic_pass') || null
          : null,

      login: (response: LoginResponse) => {
        localStorage.setItem('access_token', response.access)
        localStorage.setItem('refresh_token', response.refresh)
        set({
          user: response.user,
          accessToken: response.access,
          refreshToken: response.refresh,
          isAuthenticated: true,
        })
      },

      logout: () => {
        const refresh = localStorage.getItem('refresh_token')
        if (refresh) authApi.logout(refresh).catch(() => {})
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem('subsonic_pass')
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          subsonicPassword: null,
        })
      },

      setUser: (user: User) => set({ user }),

      setSubsonicCredentials: (password: string | null) => {
        if (typeof window !== 'undefined') {
          if (password) {
            window.sessionStorage.setItem('subsonic_pass', password)
          } else {
            window.sessionStorage.removeItem('subsonic_pass')
          }
        }
        set({ subsonicPassword: password })
      },
    }),
    {
      name: 'sonata-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        // subsonicPassword is intentionally NOT persisted
      }),
    }
  )
)
