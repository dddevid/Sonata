import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import Layout from '@/components/Layout'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Home from '@/pages/Home'
import Artists from '@/pages/Artists'
import ArtistDetail from '@/pages/ArtistDetail'
import Albums from '@/pages/Albums'
import AlbumDetail from '@/pages/AlbumDetail'
import Playlists from '@/pages/Playlists'
import PlaylistDetail from '@/pages/PlaylistDetail'
import Search from '@/pages/Search'
import Admin from '@/pages/Admin'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  // Wait for persisted user to rehydrate before rendering pages that
  // generate authenticated media URLs (covers/streams).
  if (!user) return null
  return <>{children}</>
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user)
  if (!user?.isAdmin) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  useEffect(() => {
    // One-time cleanup for old corrupted sessions that still have the placeholder
    if (localStorage.getItem('subsonic_pass') === 'sonata_placeholder') {
      useAuthStore.getState().logout()
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Home />} />
          <Route path="artists" element={<Artists />} />
          <Route path="artists/:id" element={<ArtistDetail />} />
          <Route path="albums" element={<Albums />} />
          <Route path="albums/:id" element={<AlbumDetail />} />
          <Route path="playlists" element={<Playlists />} />
          <Route path="playlists/:id" element={<PlaylistDetail />} />
          <Route path="search" element={<Search />} />
          <Route
            path="admin/*"
            element={
              <RequireAdmin>
                <Admin />
              </RequireAdmin>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
