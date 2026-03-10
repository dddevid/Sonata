/**
 * Typed wrappers around the REST API (/api/*) used by the web UI.
 */
import api from './client'
import { useAuthStore } from '@/stores/authStore'
import type {
  Artist, Album, Song, Genre, Playlist, RadioStation,
  MusicFolder, ScanStatus, Stats, User, ServerInfo, LoginResponse,
} from '@/types'
import { md5, generateSalt } from '@/utils/crypto'

function getSubsonicAuth() {
  const state = useAuthStore.getState()
  let username = state.user?.username || ''
  let pass = state.subsonicPassword
  if (!pass && typeof window !== 'undefined') {
    // Fallback to sessionStorage in case state was rehydrated without the in-memory value.
    pass = window.sessionStorage.getItem('subsonic_pass')
  }

  if (!username && typeof window !== 'undefined') {
    // Fallback to persisted auth state; <img>/<audio> requests can happen
    // before Zustand finishes rehydrating.
    try {
      const raw = window.localStorage.getItem('sonata-auth')
      if (raw) {
        const parsed = JSON.parse(raw)
        username = parsed?.state?.user?.username || ''
      }
    } catch {
      // ignore
    }
  }

  if (!username || !pass) {
    return { user: username, pass: '', jwt: state.accessToken }
  }
  return { user: username, pass, jwt: state.accessToken }
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  serverInfo: () => api.get<ServerInfo>('/api/auth/server-info/').then(r => r.data),
  login: (username: string, password: string) =>
    api.post<LoginResponse>('/api/auth/login/', { username, password }).then(r => r.data),
  register: (username: string, email: string, password: string) =>
    api.post<LoginResponse>('/api/auth/register/', { username, email, password }).then(r => r.data),
  me: () => api.get<User>('/api/auth/me/').then(r => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post('/api/auth/me/password/', { current_password, new_password }).then(r => r.data),
  logout: (refresh: string) => api.post('/api/auth/logout/', { refresh }),
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export const adminApi = {
  listUsers: () => api.get<User[]>('/api/auth/users/').then(r => r.data),
  createUser: (data: { username: string; email: string; password: string; role?: string }) =>
    api.post<User>('/api/auth/users/create/', data).then(r => r.data),
  updateUser: (id: number, data: Partial<User> & { password?: string }) =>
    api.patch<User>(`/api/auth/users/${id}/`, data).then(r => r.data),
  deleteUser: (id: number) => api.delete(`/api/auth/users/${id}/`),

  listFolders: () => api.get<MusicFolder[]>('/api/folders/').then(r => r.data),
  createFolder: (data: { name: string; path: string }) =>
    api.post<MusicFolder>('/api/folders/', data).then(r => r.data),
  updateFolder: (id: number, data: Partial<MusicFolder>) =>
    api.patch<MusicFolder>(`/api/folders/${id}/`, data).then(r => r.data),
  deleteFolder: (id: number) => api.delete(`/api/folders/${id}/`),

  startScan: () => api.post<ScanStatus>('/api/scan/start/').then(r => r.data),
  scanStatus: () => api.get<ScanStatus>('/api/scan/status/').then(r => r.data),
  stats: () => api.get<Stats>('/api/stats/').then(r => r.data),
  logs: (limit = 200) => api.get<{ logs: { ts: string; level: string; logger: string; msg: string }[] }>(`/api/logs/?limit=${limit}`).then(r => r.data),

  getNowPlaying: () => {
    const { user, pass, jwt } = getSubsonicAuth()
    const salt = generateSalt()
    const token = pass ? md5(pass + salt) : ''
    const url = `/rest/getNowPlaying?u=${encodeURIComponent(user)}&t=${token}&s=${salt}&v=1.16.1&c=sonata-ui&f=json${jwt && !pass ? `&jwt=${jwt}` : ''}`
    return api.get(url).then(r => r.data)
  }
}

// ── Music library ─────────────────────────────────────────────────────────────

export const libraryApi = {
  artists: (search?: string) =>
    api.get<Artist[]>('/api/artists/', { params: search ? { search } : {} }).then(r => r.data),
  artist: (id: number) =>
    api.get<Artist & { albums: Album[] }>(`/api/artists/${id}/`).then(r => r.data),

  albums: (sort = 'name', search?: string) =>
    api.get<Album[]>('/api/albums/', { params: { sort, ...(search ? { search } : {}) } }).then(r => r.data),
  album: (id: number) =>
    api.get<Album & { songs: Song[] }>(`/api/albums/${id}/`).then(r => r.data),

  songs: (search?: string) =>
    api.get<Song[]>('/api/songs/', { params: search ? { search } : {} }).then(r => r.data),
  song: (id: number) => api.get<Song>(`/api/songs/${id}/`).then(r => r.data),
}

// ── Playlists ─────────────────────────────────────────────────────────────────

export const playlistApi = {
  list: () => api.get<Playlist[]>('/api/playlists/').then(r => r.data),
  get: (id: number) =>
    api.get<Playlist & { songs: Song[] }>(`/api/playlists/${id}/`).then(r => r.data),
  create: (name: string, comment = '') =>
    api.post<Playlist>('/api/playlists/', { name, comment }).then(r => r.data),
  update: (id: number, data: Partial<Playlist>) =>
    api.patch<Playlist>(`/api/playlists/${id}/`, data).then(r => r.data),
  delete: (id: number) => api.delete(`/api/playlists/${id}/`),
  addSongs: (id: number, songIds: number[]) =>
    api.post(`/api/playlists/${id}/songs/`, { song_ids: songIds }),
}

// ── Radio ─────────────────────────────────────────────────────────────────────

export const radioApi = {
  list: () => api.get<RadioStation[]>('/api/radio/').then(r => r.data),
  create: (data: Partial<RadioStation>) =>
    api.post<RadioStation>('/api/radio/', data).then(r => r.data),
  update: (id: number, data: Partial<RadioStation>) =>
    api.patch<RadioStation>(`/api/radio/${id}/`, data).then(r => r.data),
  delete: (id: number) => api.delete(`/api/radio/${id}/`),
}

// ── Stream URL helpers ────────────────────────────────────────────────────────

export function streamUrl(songId: number): string {
  const { user, pass, jwt } = getSubsonicAuth()
  const salt = generateSalt()
  const token = pass ? md5(pass + salt) : ''
  return `/rest/stream?id=${songId}&u=${encodeURIComponent(user)}&t=${token}&s=${salt}&v=1.16.1&c=sonata-ui&f=json${jwt && !pass ? `&jwt=${jwt}` : ''}`
}

export function coverArtUrl(id: string, size?: number): string {
  const { user, pass, jwt } = getSubsonicAuth()
  const salt = generateSalt()
  const token = pass ? md5(pass + salt) : ''
  const sizeParam = size ? `&size=${size}` : ''
  return `/rest/getCoverArt?id=${encodeURIComponent(id)}&u=${encodeURIComponent(user)}&t=${token}&s=${salt}&v=1.16.1&c=sonata-ui${sizeParam}${jwt && !pass ? `&jwt=${jwt}` : ''}`
}
