import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search as SearchIcon, Play } from 'lucide-react'
import { libraryApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import CoverArt from '@/components/CoverArt'

type Tab = 'artists' | 'albums' | 'songs'

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function Search() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [tab, setTab] = useState<Tab>('artists')
  const inputRef = useRef<HTMLInputElement>(null)
  const { playSong } = usePlayerStore()

  // Debounce
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(t)
  }, [query])

  const enabled = debouncedQuery.trim().length >= 2

  const { data: artists = [] } = useQuery({
    queryKey: ['search', 'artists', debouncedQuery],
    queryFn: () => libraryApi.artists(debouncedQuery),
    enabled,
  })

  const { data: albums = [] } = useQuery({
    queryKey: ['search', 'albums', debouncedQuery],
    queryFn: () => libraryApi.albums('name', debouncedQuery),
    enabled,
  })

  const { data: songs = [] } = useQuery({
    queryKey: ['search', 'songs', debouncedQuery],
    queryFn: () => libraryApi.songs(debouncedQuery),
    enabled,
  })

  useEffect(() => { inputRef.current?.focus() }, [])

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: 'artists', label: 'Artists', count: artists.length },
    { key: 'albums', label: 'Albums', count: albums.length },
    { key: 'songs', label: 'Songs', count: songs.length },
  ]

  return (
    <div className="p-6 animate-fade-in">
      {/* Search bar */}
      <div className="relative max-w-xl mb-6">
        <SearchIcon size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          ref={inputRef}
          type="text"
          placeholder="Search artists, albums, songs…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-11 pr-4 py-3 bg-elevated border border-border rounded-xl text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light text-sm"
        />
      </div>

      {!enabled && (
        <div className="flex flex-col items-center justify-center py-24">
          <SearchIcon size={40} className="text-text-muted mb-3" />
          <p className="text-text-secondary text-sm">Type at least 2 characters to search</p>
        </div>
      )}

      {enabled && (
        <>
          {/* Tabs */}
          <div className="flex gap-1 mb-6 border-b border-border">
            {tabs.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  tab === t.key
                    ? 'border-primary-light text-primary-light'
                    : 'border-transparent text-text-muted hover:text-text-primary'
                }`}
              >
                {t.label}
                {t.count > 0 && (
                  <span className="ml-1.5 text-xs bg-elevated px-1.5 py-0.5 rounded-full">{t.count}</span>
                )}
              </button>
            ))}
          </div>

          {/* Artists */}
          {tab === 'artists' && (
            artists.length === 0 ? (
              <p className="text-text-muted text-sm py-8 text-center">No artists found</p>
            ) : (
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2">
                {artists.map((artist) => (
                  <Link
                    key={artist.id}
                    to={`/artists/${artist.id}`}
                    className="group flex flex-col items-center gap-3 p-4 rounded-xl hover:bg-elevated transition-colors"
                  >
                    <div className="w-20 h-20 rounded-full bg-surface flex items-center justify-center overflow-hidden">
                      {artist.id ? (
                        <CoverArt artId={`ar-${artist.id}`} size={300} alt={artist.name} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-2xl">🎤</span>
                      )}
                    </div>
                    <p className="text-xs font-medium text-text-primary truncate max-w-[100px] text-center">{artist.name}</p>
                  </Link>
                ))}
              </div>
            )
          )}

          {/* Albums */}
          {tab === 'albums' && (
            albums.length === 0 ? (
              <p className="text-text-muted text-sm py-8 text-center">No albums found</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {albums.map((album) => (
                  <Link key={album.id} to={`/albums/${album.id}`} className="group">
                    <div className="aspect-square rounded-xl overflow-hidden bg-surface mb-2 shadow-md">
                      {album.id ? (
                        <CoverArt
                          artId={`al-${album.id}`}
                          size={600}
                          alt={album.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-3xl">💿</div>
                      )}
                    </div>
                    <p className="text-sm font-medium text-text-primary truncate">{album.name}</p>
                    <p className="text-xs text-text-muted truncate">{album.artist}</p>
                  </Link>
                ))}
              </div>
            )
          )}

          {/* Songs */}
          {tab === 'songs' && (
            songs.length === 0 ? (
              <p className="text-text-muted text-sm py-8 text-center">No songs found</p>
            ) : (
              <div className="space-y-0.5">
                {songs.map((song) => (
                  <div
                    key={song.id}
                    onClick={() => playSong(song)}
                    className="group flex items-center gap-4 px-4 py-2.5 rounded-lg hover:bg-elevated cursor-pointer transition-colors"
                  >
                    <div className="w-10 h-10 rounded-md bg-surface flex items-center justify-center overflow-hidden flex-shrink-0">
                      {song.id ? (
                        <CoverArt artId={`mf-${song.id}`} size={300} alt={song.title} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-lg">🎵</span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-text-primary truncate">{song.title}</p>
                      <p className="text-xs text-text-muted truncate">
                        {song.artist}{song.album && ` · ${song.album}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Play size={14} className="text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                      <span className="text-xs text-text-muted tabular-nums">{formatDuration(song.duration)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </>
      )}
    </div>
  )
}
