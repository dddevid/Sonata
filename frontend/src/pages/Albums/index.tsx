import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { libraryApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import AlbumCard from '@/components/AlbumCard'

type SortOption = '-created' | 'name' | '-name' | 'year' | '-year'

const SORT_LABELS: Record<SortOption, string> = {
  '-created': 'Recently Added',
  'name': 'Name (A–Z)',
  '-name': 'Name (Z–A)',
  'year': 'Year (Oldest)',
  '-year': 'Year (Newest)',
}

export default function Albums() {
  const [sort, setSort] = useState<SortOption>('-created')
  const { playQueue } = usePlayerStore()

  const { data: albums = [], isLoading } = useQuery({
    queryKey: ['albums', sort],
    queryFn: () => libraryApi.albums(sort),
  })

  const handlePlayAlbum = async (albumId: number) => {
    try {
      const album = await libraryApi.album(albumId)
      if (album.songs?.length) {
        playQueue(album.songs)
      }
    } catch {}
  }

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Albums</h1>
          <p className="text-sm text-text-secondary mt-1">
            {albums.length} album{albums.length !== 1 ? 's' : ''}
          </p>
        </div>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortOption)}
          className="bg-elevated border border-border text-text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-primary-light"
        >
          {(Object.keys(SORT_LABELS) as SortOption[]).map((key) => (
            <option key={key} value={key}>{SORT_LABELS[key]}</option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} className="aspect-square bg-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && albums.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24">
          <span className="text-4xl mb-3">💿</span>
          <p className="text-text-secondary text-sm">No albums found</p>
        </div>
      )}

      {!isLoading && albums.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {albums.map((album) => (
            <AlbumCard key={album.id} album={album} onPlay={() => handlePlayAlbum(album.id)} />
          ))}
        </div>
      )}
    </div>
  )
}
