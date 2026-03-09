import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { libraryApi } from '@/api'
import type { Artist } from '@/types'
import CoverArt from '@/components/CoverArt'

function ArtistCard({ artist }: { artist: Artist }) {
  return (
    <Link
      to={`/artists/${artist.id}`}
      className="group flex flex-col items-center gap-3 p-4 rounded-xl hover:bg-elevated transition-colors"
    >
      <div className="w-24 h-24 rounded-full bg-surface flex items-center justify-center overflow-hidden shadow-lg">
        {artist.id ? (
          <CoverArt
            artId={`ar-${artist.id}`}
            size={300}
            alt={artist.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <span className="text-3xl select-none">🎤</span>
        )}
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary truncate max-w-[120px]">{artist.name}</p>
        <p className="text-xs text-text-muted mt-0.5">{artist.album_count} album{artist.album_count !== 1 ? 's' : ''}</p>
      </div>
    </Link>
  )
}

export default function Artists() {
  const [query, setQuery] = useState('')

  const { data: artists = [], isLoading } = useQuery({
    queryKey: ['artists'],
    queryFn: () => libraryApi.artists(),
  })

  const filtered = query
    ? artists.filter((a) => a.name.toLowerCase().includes(query.toLowerCase()))
    : artists

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Artists</h1>
          <p className="text-sm text-text-secondary mt-1">
            {artists.length} artist{artists.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Filter artists…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-8 pr-4 py-2 text-sm bg-elevated border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
          />
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2">
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-3 p-4">
              <div className="w-24 h-24 rounded-full bg-elevated animate-pulse" />
              <div className="h-3 w-20 bg-elevated rounded animate-pulse" />
            </div>
          ))}
        </div>
      )}

      {!isLoading && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24">
          <span className="text-4xl mb-3">🎤</span>
          <p className="text-text-secondary text-sm">{query ? 'No artists match your search' : 'No artists found'}</p>
        </div>
      )}

      {!isLoading && filtered.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2">
          {filtered.map((artist) => (
            <ArtistCard key={artist.id} artist={artist} />
          ))}
        </div>
      )}
    </div>
  )
}
