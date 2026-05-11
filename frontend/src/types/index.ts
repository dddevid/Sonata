// Core domain types mirroring the OpenSubsonic API

export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  isAdmin: boolean
  max_bit_rate: number
  avatar: string | null
  scrobbling_enabled: boolean
  stream_role: boolean
  download_role: boolean
  upload_role: boolean
  playlist_role: boolean
  share_role: boolean
  date_joined: string
}

export interface Artist {
  id: number
  name: string
  album_count: number
  biography: string
  image_url: string
  mb_id: string
}

export interface Album {
  id: number
  name: string
  artist: number
  artist_name: string
  genre: number | null
  genre_name: string | null
  year: number | null
  song_count: number
  duration: number
  created: string
  cover_art_path: string
}

export interface Song {
  id: number
  title: string
  artist: number
  artist_name: string
  album: number
  album_name: string
  genre: number | null
  genre_name: string | null
  track: number | null
  disc_number: number | null
  year: number | null
  duration: number
  bit_rate: number
  size: number
  suffix: string
  content_type: string
  path: string
  play_count: number
  last_played: string | null
  created: string
}

export interface Genre {
  id: number
  name: string
  song_count: number
  album_count: number
}

export interface Playlist {
  id: number
  name: string
  owner: number
  owner_name: string
  comment: string
  public: boolean
  song_count: number
  duration: number
  created: string
  changed: string
  songs?: Song[]
}

export interface RadioStation {
  id: number
  name: string
  stream_url: string
  home_page_url: string
}

export interface ScanStatus {
  is_scanning: boolean
  count: number
  folder_count: number
  last_scan: string | null
  scanned_files?: number
  total_files?: number
}

export interface MusicFolder {
  id: number
  name: string
  path: string
  enabled: boolean
  created: string
}

export interface ServerInfo {
  name: string
  version: string
  users_exist: boolean
  allow_self_register?: boolean
}

export interface Stats {
  artists: number
  albums: number
  songs: number
  users: number
  folders: number
  genres: number
  playlists: number
}

export interface QueueItem extends Song {
  queueId: string
}

export type RepeatMode = 'none' | 'all' | 'one'

export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginResponse {
  user: User
  access: string
  refresh: string
}

export interface ServerSettings {
  allow_self_register: boolean
  server_name: string
  debug: boolean
  cors_allowed_origins: string
  access_token_lifetime_minutes: number
  refresh_token_lifetime_days: number
  throttle_user_rate: string
  throttle_anon_rate: string
  // LDAP
  ldap_enabled: boolean
  ldap_server_uri: string
  ldap_bind_dn: string
  ldap_bind_password: string
  ldap_user_search_base: string
  ldap_user_search_filter: string
  ldap_group_search_base: string
  ldap_group_search_filter: string
  ldap_require_group: string
  ldap_group_type: string
  ldap_superuser_group: string
}
