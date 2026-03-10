"""media.py — stream, download, getCoverArt, getLyrics, getAvatar"""

import os
import re
import mimetypes
import subprocess
import xml.etree.ElementTree as ET
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error
from apps.music.models import Song, Album, Artist, ActiveStream


AUDIO_CONTENT_TYPES = {
    'mp3': 'audio/mpeg',
    'flac': 'audio/flac',
    'ogg': 'audio/ogg',
    'oga': 'audio/ogg',
    'opus': 'audio/opus',
    'm4a': 'audio/mp4',
    'aac': 'audio/aac',
    'wav': 'audio/wav',
    'aiff': 'audio/aiff',
    'wma': 'audio/x-ms-wma',
}

CHUNK_SIZE = 65536  # 64 KB


def _iter_file(path, start=0, end=None):
    with open(path, 'rb') as f:
        f.seek(start)
        remaining = (end - start + 1) if end is not None else None
        while True:
            chunk_size = CHUNK_SIZE if remaining is None else min(CHUNK_SIZE, remaining)
            data = f.read(chunk_size)
            if not data:
                break
            yield data
            if remaining is not None:
                remaining -= len(data)
                if remaining <= 0:
                    break


def _serve_file(request, path, content_type):
    if not os.path.exists(path):
        return HttpResponse(status=404)

    file_size = os.path.getsize(path)
    range_header = request.META.get('HTTP_RANGE', '').strip()

    if range_header:
        match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            first = int(match.group(1))
            last = int(match.group(2)) if match.group(2) else file_size - 1
            last = min(last, file_size - 1)
            length = last - first + 1
            response = StreamingHttpResponse(
                _iter_file(path, first, last),
                status=206,
                content_type=content_type,
            )
            response['Content-Range'] = f'bytes {first}-{last}/{file_size}'
            response['Content-Length'] = length
            response['Accept-Ranges'] = 'bytes'
            return response

    response = StreamingHttpResponse(_iter_file(path), content_type=content_type)
    response['Content-Length'] = file_size
    response['Accept-Ranges'] = 'bytes'
    return response


# ── stream ─────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def stream(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_id = p.get('id')
    if not song_id:
        return make_error(request, 10, 'Required parameter missing: id')

    try:
        song = Song.objects.get(pk=song_id)
    except (Song.DoesNotExist, ValueError):
        return make_error(request, 70, 'Song not found')

    if not os.path.exists(song.path):
        return make_error(request, 70, 'File not found on disk')

    max_bit_rate = int(p.get('maxBitRate', 0))
    fmt = p.get('format', '').lower() or song.suffix

    # Increment play count
    song.play_count += 1
    from django.utils import timezone
    song.last_played = timezone.now()
    song.save(update_fields=['play_count', 'last_played'])

    client = p.get('c', 'Unknown')
    ActiveStream.objects.update_or_create(
        user=request.subsonic_user,
        client=client,
        defaults={'song': song}
    )

    # Decide whether to transcode
    needs_transcode = (
        fmt not in ('', 'raw', song.suffix) or
        (max_bit_rate > 0 and song.bit_rate > max_bit_rate)
    )

    if needs_transcode:
        return _transcode_stream(song, fmt or 'mp3', max_bit_rate)

    content_type = AUDIO_CONTENT_TYPES.get(song.suffix, song.content_type or 'application/octet-stream')
    return _serve_file(request, song.path, content_type)


def _transcode_stream(song, fmt, max_bit_rate):
    """Stream transcoded audio via FFmpeg pipe."""
    bit_rate_arg = f'{max_bit_rate}k' if max_bit_rate > 0 else '128k'

    codec_map = {
        'mp3': ('libmp3lame', 'audio/mpeg'),
        'ogg': ('libvorbis', 'audio/ogg'),
        'opus': ('libopus', 'audio/opus'),
        'aac': ('aac', 'audio/aac'),
    }
    codec, mime = codec_map.get(fmt, ('libmp3lame', 'audio/mpeg'))

    cmd = [
        'ffmpeg', '-v', 'quiet', '-i', song.path,
        '-acodec', codec, '-ab', bit_rate_arg, '-f', fmt, '-',
    ]

    def generate():
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                chunk = proc.stdout.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
            proc.wait()
        except FileNotFoundError:
            # FFmpeg not installed — fall back to raw
            with open(song.path, 'rb') as f:
                while True:
                    data = f.read(CHUNK_SIZE)
                    if not data:
                        break
                    yield data

    response = StreamingHttpResponse(generate(), content_type=mime)
    response['X-Content-Type-Options'] = 'nosniff'
    return response


# ── download ───────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def download(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_id = p.get('id')
    if not song_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        song = Song.objects.get(pk=song_id)
    except (Song.DoesNotExist, ValueError):
        return make_error(request, 70, 'Song not found')

    if not os.path.exists(song.path):
        return make_error(request, 70, 'File not found on disk')

    filename = os.path.basename(song.path)
    content_type = AUDIO_CONTENT_TYPES.get(song.suffix, 'application/octet-stream')
    response = FileResponse(open(song.path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = os.path.getsize(song.path)
    return response


# ── hls (stub) ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def hls(request):
    return make_error(request, 30, 'HLS not supported')


def serve_cover_art(art_id, size=None):
    cover_path = None
    
    def _add_cache_header(response):
        # Cache for 30 days
        response['Cache-Control'] = 'public, max-age=2592000'
        return response

    if art_id.startswith('al-'):
        try:
            album = Album.objects.get(pk=art_id[3:])
            cover_path = album.cover_art_path
        except (Album.DoesNotExist, ValueError):
            pass
    elif art_id.startswith('mf-'):
        try:
            song = Song.objects.select_related('album').get(pk=art_id[3:])
            cover_path = song.album.cover_art_path if song.album_id else None
        except (Song.DoesNotExist, ValueError):
            pass
    elif art_id.startswith('ar-'):
        try:
            artist = Artist.objects.get(pk=art_id[3:])
            if artist.image_path and os.path.exists(artist.image_path):
                cover_path = artist.image_path
            elif artist.image_url:
                import requests
                from django.conf import settings
                try:
                    r = requests.get(artist.image_url, timeout=10)
                    r.raise_for_status()
                    
                    media_root = getattr(settings, 'MEDIA_ROOT', './media')
                    art_dir = os.path.join(media_root, 'artist-images')
                    os.makedirs(art_dir, exist_ok=True)
                    
                    ext = '.jpg'
                    if 'png' in artist.image_url.lower() or 'png' in r.headers.get('content-type', '').lower():
                        ext = '.png'
                    file_path = os.path.join(art_dir, f'ar-{artist.pk}{ext}')
                    
                    with open(file_path, 'wb') as f:
                        f.write(r.content)
                        
                    artist.image_path = file_path
                    artist.save(update_fields=['image_path'])
                    cover_path = file_path
                except Exception:
                    pass
        except (Artist.DoesNotExist, ValueError):
            pass
    elif art_id.startswith('pl-'):
        # Playlist — try to create a collage or return the first song's album art
        from apps.music.models import Playlist
        try:
            pl = Playlist.objects.get(pk=art_id[3:])
            entries = pl.entries.select_related('song__album').order_by('position')
            paths = []
            for entry in entries:
                if getattr(entry.song, 'album', None) and entry.song.album.cover_art_path:
                    p = entry.song.album.cover_art_path
                    if os.path.exists(p) and p not in paths:
                        paths.append(p)
                        if len(paths) == 4:
                            break
            
            if len(paths) >= 4:
                return _add_cache_header(_generate_playlist_collage(paths, size))
            elif len(paths) > 0:
                cover_path = paths[0]
            else:
                return _add_cache_header(_sonata_placeholder())
        except (Playlist.DoesNotExist, ValueError):
            return _add_cache_header(_sonata_placeholder())

    if cover_path and os.path.exists(cover_path):
        if size:
            try:
                from PIL import Image
                import io
                img = Image.open(cover_path).convert('RGB')
                img.thumbnail((int(size), int(size)))
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                buf.seek(0)
                return _add_cache_header(HttpResponse(buf.read(), content_type='image/jpeg'))
            except Exception:
                pass
        return _add_cache_header(FileResponse(open(cover_path, 'rb'), content_type='image/jpeg'))

    # Default: return embedded cover art from file tags
    if art_id.startswith('al-') or art_id.startswith('mf-'):
        song_id = None
        if art_id.startswith('al-'):
            song = Song.objects.filter(album_id=art_id[3:]).first()
            if song:
                song_id = song.pk
        else:
            song_id = art_id[3:]

        if song_id:
            try:
                song = Song.objects.get(pk=song_id)
                cover_data, mime = _extract_embedded_cover(song.path)
                if cover_data:
                    return _add_cache_header(HttpResponse(cover_data, content_type=mime))
            except Song.DoesNotExist:
                pass

    return _add_cache_header(_default_cover())


# ── getCoverArt (Subsonic) ─────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_cover_art(request):
    p = request.GET if request.method == 'GET' else request.POST
    art_id = p.get('id', '')
    size = p.get('size')
    return serve_cover_art(art_id, size)


def _extract_embedded_cover(file_path):
    """Extract embedded cover art using mutagen."""
    try:
        import mutagen
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4

        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.mp3':
            audio = ID3(file_path)
            for key in audio.keys():
                if key.startswith('APIC'):
                    apic = audio[key]
                    return apic.data, apic.mime
        elif ext == '.flac':
            audio = FLAC(file_path)
            if audio.pictures:
                pic = audio.pictures[0]
                return pic.data, pic.mime
        elif ext in ('.m4a', '.mp4', '.aac'):
            audio = MP4(file_path)
            if 'covr' in audio:
                cover = audio['covr'][0]
                mime = 'image/jpeg' if cover.imageformat == 13 else 'image/png'
                return bytes(cover), mime
    except Exception:
        pass
    return None, None


def _default_cover():
    """Return a minimal placeholder image."""
    svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" fill="#1c1c1c"/>
  <circle cx="100" cy="100" r="60" fill="none" stroke="#333" stroke-width="2"/>
  <circle cx="100" cy="100" r="20" fill="#333"/>
  <path d="M110 60 L130 55 L130 80 L110 85 Z" fill="#555"/>
</svg>'''
    return HttpResponse(svg, content_type='image/svg+xml')


def _sonata_placeholder():
    """Return the Sonata logo as a placeholder."""
    # The logo is in the root of the project
    svg_path = os.path.join(settings.BASE_DIR.parent, 'Sonata Logo.svg')
    if os.path.exists(svg_path):
        return FileResponse(open(svg_path, 'rb'), content_type='image/svg+xml')
    return _default_cover()


def _generate_playlist_collage(paths, size=None):
    from PIL import Image
    import io
    
    target_size = int(size) if size else 500
    half = target_size // 2
    
    collage = Image.new('RGB', (target_size, target_size))
    
    try:
        # Paste 4 images in a 2x2 grid
        positions = [(0, 0), (half, 0), (0, half), (half, half)]
        
        for i, path in enumerate(paths):
            img = Image.open(path).convert('RGB')
            # Use LANCZOS if available, otherwise fallback (for older PIL)
            resample = getattr(Image, 'Resampling', Image).LANCZOS
            img = img.resize((half, half), resample)
            collage.paste(img, positions[i])
            
        buf = io.BytesIO()
        collage.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        return HttpResponse(buf.read(), content_type='image/jpeg')
    except Exception:
        return _sonata_placeholder()


# ── getLyrics ──────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_lyrics(request):
    def xml_builder(root):
        ET.SubElement(root, 'lyrics')
    return make_ok(request, data={'lyrics': {}}, xml_builder=xml_builder)


# ── getAvatar ──────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_avatar(request):
    p = request.GET if request.method == 'GET' else request.POST
    username = p.get('username', '')
    from apps.accounts.models import User
    try:
        user = User.objects.get(username=username)
        if user.avatar and os.path.exists(user.avatar.path):
            return FileResponse(open(user.avatar.path, 'rb'), content_type='image/jpeg')
    except User.DoesNotExist:
        pass
    return _default_cover()
