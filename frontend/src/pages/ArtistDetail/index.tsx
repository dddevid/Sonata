import { useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { libraryApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import AlbumCard from '@/components/AlbumCard'
import CoverArt from '@/components/CoverArt'
import { useCoverArtBlob } from '@/hooks/useCoverArt'

export default function ArtistDetail() {
  const { id } = useParams<{ id: string }>()
  const { playQueue } = usePlayerStore()

  const { data: artist, isLoading, error } = useQuery({
    queryKey: ['artist', id],
    queryFn: () => libraryApi.artist(Number(id)),
    enabled: !!id,
  })

  const handlePlayAlbum = async (albumId: number) => {
    try {
      const album = await libraryApi.album(albumId)
      if (album.songs?.length) {
        playQueue(album.songs)
      }
    } catch {}
  }

  if (isLoading) {
    return (
      <div className="p-6 animate-fade-in">
        <div className="h-6 w-32 bg-elevated rounded animate-pulse mb-8" />
        <div className="flex items-end gap-8 mb-10">
          <div className="w-40 h-40 rounded-full bg-elevated animate-pulse" />
          <div className="space-y-3">
            <div className="h-8 w-64 bg-elevated rounded animate-pulse" />
            <div className="h-4 w-32 bg-elevated rounded animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="aspect-square bg-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !artist) {
    return (
      <div className="p-6 flex flex-col items-center justify-center py-24">
        <p className="text-text-secondary">Artist not found</p>
        <Link to="/artists" className="mt-4 text-sm text-primary-light hover:underline">← Back to Artists</Link>
      </div>
    )
  }

  const bgArtId = artist.albums?.[0]?.id ? `al-${artist.albums[0].id}` : undefined
  const { data: bgBlob } = useCoverArtBlob(bgArtId, 400)
  const bgUrl = useMemo(() => (bgBlob ? URL.createObjectURL(bgBlob) : null), [bgBlob])
  useEffect(() => {
    return () => {
      if (bgUrl) URL.revokeObjectURL(bgUrl)
    }
  }, [bgUrl])

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <div className="relative">
        {/* Background blur from cover */}
        {bgUrl && (
          <div
            className="absolute inset-0 opacity-20 bg-cover bg-center blur-3xl scale-110"
            style={{ backgroundImage: `url(${bgUrl})` }}
          />
        )}
        <div className="relative px-6 py-10 flex items-end gap-8">
          <div className="w-40 h-40 rounded-full bg-surface flex items-center justify-center overflow-hidden shadow-2xl flex-shrink-0">
            {artist.id ? (
              <CoverArt artId={`ar-${artist.id}`} size={600} alt={artist.name} className="w-full h-full object-cover" />
            ) : (
              <span className="text-5xl">🎤</span>
            )}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Artist</p>
            <h1 className="text-4xl font-bold text-text-primary">{artist.name}</h1>
            <p className="text-sm text-text-secondary mt-2">
              {artist.album_count} album{artist.album_count !== 1 ? 's' : ''}
              {typeof (artist as any).song_count === 'number' && ` · ${(artist as any).song_count} songs`}
            </p>
          </div>
        </div>
      </div>

      <div className="px-6 pb-6 space-y-8 mt-2">
        <Link to="/artists" className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors">
          <ArrowLeft size={12} /> All Artists
        </Link>

        {artist.albums && artist.albums.length > 0 && (
          <section>
            <h2 className="text-base font-semibold text-text-primary mb-4">Albums</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {artist.albums.map((album) => (
                <AlbumCard key={album.id} album={album} onPlay={() => handlePlayAlbum(album.id)} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
