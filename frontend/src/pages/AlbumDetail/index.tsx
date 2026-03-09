import { useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Play, Shuffle, Clock, ArrowLeft } from 'lucide-react'
import { libraryApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import type { Song } from '@/types'
import CoverArt from '@/components/CoverArt'
import { useCoverArtBlob } from '@/hooks/useCoverArt'

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function SongRow({
  song,
  index,
  isPlaying,
  onPlay,
}: {
  song: Song
  index: number
  isPlaying: boolean
  onPlay: () => void
}) {
  return (
    <div
      onClick={onPlay}
      className={`group grid grid-cols-[2rem_1fr_auto] gap-4 items-center px-4 py-2 rounded-lg cursor-pointer transition-colors hover:bg-elevated ${
        isPlaying ? 'bg-elevated' : ''
      }`}
    >
      {/* Track number / play indicator */}
      <div className="text-center">
        {isPlaying ? (
          <span className="text-primary-light text-xs">♪</span>
        ) : (
          <>
            <span className="text-text-muted text-xs group-hover:hidden">{song.track || index + 1}</span>
            <Play size={12} className="text-text-primary hidden group-hover:block mx-auto" />
          </>
        )}
      </div>

      {/* Title */}
      <div className="min-w-0">
        <p className={`text-sm font-medium truncate ${isPlaying ? 'text-primary-light' : 'text-text-primary'}`}>
          {song.title}
        </p>
      </div>

      {/* Duration */}
      <div className="text-xs text-text-muted tabular-nums">
        {formatDuration(song.duration)}
      </div>
    </div>
  )
}

export default function AlbumDetail() {
  const { id } = useParams<{ id: string }>()
  const { playQueue, playSong, currentSong } = usePlayerStore()

  const { data: album, isLoading, error } = useQuery({
    queryKey: ['album', id],
    queryFn: () => libraryApi.album(Number(id)),
    enabled: !!id,
  })

  const handlePlayAll = () => {
    if (album?.songs?.length) {
      playQueue(album.songs)
    }
  }

  const handleShuffle = () => {
    if (album?.songs?.length) {
      const shuffled = [...album.songs].sort(() => Math.random() - 0.5)
      playQueue(shuffled)
    }
  }

  const totalDuration = album?.songs?.reduce((acc, s) => acc + s.duration, 0) ?? 0

  if (isLoading) {
    return (
      <div className="p-6 animate-fade-in">
        <div className="flex items-end gap-8 mb-8">
          <div className="w-48 h-48 rounded-xl bg-elevated animate-pulse flex-shrink-0" />
          <div className="space-y-3 flex-1">
            <div className="h-8 w-64 bg-elevated rounded animate-pulse" />
            <div className="h-4 w-40 bg-elevated rounded animate-pulse" />
            <div className="h-4 w-24 bg-elevated rounded animate-pulse" />
          </div>
        </div>
        <div className="space-y-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="h-10 bg-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !album) {
    return (
      <div className="p-6 flex flex-col items-center justify-center py-24">
        <p className="text-text-secondary">Album not found</p>
        <Link to="/albums" className="mt-4 text-sm text-primary-light hover:underline">← Back to Albums</Link>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <div className="relative">
        <AlbumHeroBackground albumId={album?.id} />
        <div className="relative px-6 py-10 flex items-end gap-8 z-10">
          <div className="w-48 h-48 rounded-xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.5)] flex-shrink-0 bg-elevated border border-border/50 transition-transform duration-300 hover:scale-105">
            {album.id ? (
              <CoverArt artId={`al-${album.id}`} size={600} alt={album.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-5xl opacity-50">💿</div>
            )}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Album</p>
            <h1 className="text-4xl font-bold text-text-primary leading-tight">{album.name}</h1>
            <Link
              to={`/artists/${album.artist}`}
              className="text-lg text-text-secondary hover:text-text-primary transition-colors mt-1 inline-block"
            >
              {album.artist_name}
            </Link>
            <p className="text-sm text-text-muted mt-2">
              {album.year && `${album.year} · `}
              {album.song_count} song{album.song_count !== 1 ? 's' : ''} · {formatDuration(totalDuration)}
              {album.genre && ` · ${album.genre}`}
            </p>
            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={handlePlayAll}
                className="flex items-center gap-2 bg-primary-light hover:bg-primary text-white text-sm font-semibold px-6 py-2.5 rounded-full transition-colors"
              >
                <Play size={14} fill="white" /> Play
              </button>
              <button
                onClick={handleShuffle}
                className="flex items-center gap-2 bg-elevated hover:bg-border text-text-primary text-sm font-semibold px-5 py-2.5 rounded-full transition-colors"
              >
                <Shuffle size={14} /> Shuffle
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 pb-6">
        <Link to="/albums" className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors mb-6">
          <ArrowLeft size={12} /> All Albums
        </Link>

        {/* Songs */}
        {album.songs && album.songs.length > 0 && (
          <div>
            {/* Column headers */}
            <div className="grid grid-cols-[2rem_1fr_auto] gap-4 items-center px-4 py-1 mb-1 border-b border-border">
              <span className="text-xs text-text-muted text-center">#</span>
              <span className="text-xs text-text-muted">Title</span>
              <Clock size={12} className="text-text-muted" />
            </div>
            <div className="space-y-0.5 mt-2">
              {album.songs.map((song, i) => (
                <SongRow
                  key={song.id}
                  song={song}
                  index={i}
                  isPlaying={currentSong?.id === song.id}
                  onPlay={() => playQueue(album.songs!, i)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function AlbumHeroBackground({ albumId }: { albumId?: number }) {
  const artId = albumId ? `al-${albumId}` : undefined
  const { data: blob } = useCoverArtBlob(artId, 400)
  const objectUrl = useMemo(() => (blob ? URL.createObjectURL(blob) : null), [blob])
  useEffect(() => {
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [objectUrl])

  if (!objectUrl) return null
  return (
    <div
      className="absolute inset-0 opacity-20 bg-cover bg-center blur-3xl scale-110"
      style={{ backgroundImage: `url(${objectUrl})` }}
    />
  )
}
