import { useEffect, useMemo } from 'react'
import { useCoverArtBlob } from '@/hooks/useCoverArt'

const DEFAULT_COVER_DATA_URL =
  'data:image/svg+xml;charset=utf-8,' +
  encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" fill="#1c1c1c"/>
  <circle cx="100" cy="100" r="60" fill="none" stroke="#333" stroke-width="2"/>
  <circle cx="100" cy="100" r="20" fill="#333"/>
  <path d="M110 60 L130 55 L130 80 L110 85 Z" fill="#555"/>
</svg>
`.trim())

type Props = Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'src'> & {
  artId?: string
  size?: number
}

export default function CoverArt({ artId, size, ...imgProps }: Props) {
  const { data: blob } = useCoverArtBlob(artId, size)

  const objectUrl = useMemo(() => (blob ? URL.createObjectURL(blob) : null), [blob])
  useEffect(() => {
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [objectUrl])

  return <img {...imgProps} src={objectUrl || DEFAULT_COVER_DATA_URL} />
}
