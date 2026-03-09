import { useQuery } from '@tanstack/react-query'
import api from '@/api/client'

export function useCoverArtBlob(artId?: string, size?: number) {
  return useQuery({
    queryKey: ['coverArt', artId, size],
    enabled: !!artId,
    queryFn: async () => {
      const url = `/api/cover-art/${encodeURIComponent(artId!)}/`
      const res = await api.get(url, {
        params: size ? { size } : undefined,
        responseType: 'blob',
      })
      return res.data as Blob
    },
    staleTime: 1000 * 60 * 60, // 1h
    retry: 1,
  })
}
