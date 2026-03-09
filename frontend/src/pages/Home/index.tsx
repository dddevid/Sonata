import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { libraryApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import AlbumCard from '@/components/AlbumCard'
import type { Album, Song } from '@/types'

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-base font-semibold text-text-primary mb-4">{children}</h2>
}

function AlbumRow({ albums, onPlayAlbum }: { albums: Album[]; onPlayAlbum: (id: number) => void }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      {albums.map((album) => (
        <AlbumCard key={album.id} album={album} onPlay={() => onPlayAlbum(album.id)} />
      ))}
    </div>
  )
}

export default function Home() {
  const { playQueue } = usePlayerStore()

  const { data: recentAlbums } = useQuery({
    queryKey: ['albums', 'recent'],
    queryFn: () => libraryApi.albums('-created'),
    select: (d) => d.slice(0, 12),
  })

  const { data: allAlbumsData } = useQuery({
    queryKey: ['albums', 'random'],
    queryFn: () => libraryApi.albums('name'),
  })
  const allAlbums = useMemo(() => {
    if (!allAlbumsData) return []
    return [...allAlbumsData].sort(() => Math.random() - 0.5).slice(0, 12)
  }, [allAlbumsData])

  const handlePlayAlbum = async (albumId: number) => {
    try {
      const album = await libraryApi.album(albumId)
      if (album.songs?.length) {
        playQueue(album.songs)
      }
    } catch {}
  }

  return (
    <div className="p-6 space-y-10 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Home</h1>
        <p className="text-sm text-text-secondary mt-1">Welcome back</p>
      </div>

      {recentAlbums && recentAlbums.length > 0 && (
        <section>
          <SectionTitle>Recently Added</SectionTitle>
          <AlbumRow albums={recentAlbums} onPlayAlbum={handlePlayAlbum} />
        </section>
      )}

      {allAlbums && allAlbums.length > 0 && (
        <section>
          <SectionTitle>Discover</SectionTitle>
          <AlbumRow albums={allAlbums} onPlayAlbum={handlePlayAlbum} />
        </section>
      )}

      {(!recentAlbums || recentAlbums.length === 0) && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-elevated flex items-center justify-center mb-4">
            <span className="text-3xl">🎵</span>
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">No music yet</h3>
          <p className="text-sm text-text-secondary max-w-sm">
            Add a music folder and start a scan from the{' '}
            <a href="/admin" className="text-primary-light hover:underline">admin panel</a>.
          </p>
        </div>
      )}
    </div>
  )
}
