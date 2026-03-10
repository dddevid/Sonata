import os
import logging
import threading
import secrets
from collections import deque
from django.conf import settings
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import (
    MusicFolder, Artist, Album, Song, Genre, Playlist, PlaylistSong,
    InternetRadioStation, ScanStatus, Share,
)
from .serializers import (
    MusicFolderSerializer, ArtistSerializer, AlbumSerializer,
    SongSerializer, PlaylistSerializer, RadioStationSerializer, ScanStatusSerializer,
)

# ── In-memory log capture ──────────────────────────────────────────────────────

_LOG_BUFFER: deque = deque(maxlen=500)
_LOG_LOCK = threading.Lock()

LEVEL_COLORS = {
    'DEBUG': 'debug',
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'error',
    'CRITICAL': 'error',
}


class _MemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                'ts': self.formatter.formatTime(record, '%H:%M:%S') if self.formatter else '',
                'level': record.levelname,
                'logger': record.name,
                'msg': self.format(record),
            }
            with _LOG_LOCK:
                _LOG_BUFFER.append(entry)
        except Exception:
            pass


def _install_log_handler():
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, _MemoryLogHandler):
            return
    handler = _MemoryLogHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(logging.DEBUG)
    root.addHandler(handler)


_install_log_handler()


def _admin_required(request):
    if not request.user.is_admin_user:
        return Response({'detail': 'Admin required.'}, status=403)
    return None


# ── Music folders ──────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def music_folders(request):
    if request.method == 'GET':
        folders = MusicFolder.objects.all()
        return Response(MusicFolderSerializer(folders, many=True).data)

    err = _admin_required(request)
    if err:
        return err
    ser = MusicFolderSerializer(data=request.data)
    if ser.is_valid():
        folder = ser.save()
        return Response(MusicFolderSerializer(folder).data, status=201)
    return Response(ser.errors, status=400)


@api_view(['PATCH', 'DELETE'])
def music_folder_detail(request, folder_id):
    err = _admin_required(request)
    if err:
        return err
    try:
        folder = MusicFolder.objects.get(pk=folder_id)
    except MusicFolder.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method == 'DELETE':
        folder.delete()
        return Response(status=204)

    ser = MusicFolderSerializer(folder, data=request.data, partial=True)
    if ser.is_valid():
        ser.save()
        return Response(ser.data)
    return Response(ser.errors, status=400)


# ── Scan ───────────────────────────────────────────────────────────────────────

def _trigger_scan():
    """Scan all enabled music folders using the Scanner class (scanner.py)."""
    from .scanner import Scanner
    folders = list(MusicFolder.objects.filter(enabled=True).values_list('path', flat=True))
    scanner = Scanner()
    scanner.scan_folders(folders)


# ── Built-in Python scanner ────────────────────────────────────────────────────

_AUDIO_EXTENSIONS = {
    '.mp3', '.flac', '.ogg', '.oga', '.opus',
    '.m4a', '.mp4', '.aac', '.wav', '.aiff', '.aif', '.wma',
}


def _python_scan(folders, scan_status):
    """Walk folders, extract metadata with mutagen, upsert into DB."""
    import logging
    from mutagen import File as MutagenFile

    log = logging.getLogger(__name__)
    count = 0

    for folder_path in folders:
        if not os.path.isdir(folder_path):
            log.warning('Music folder not found on disk: %s', folder_path)
            continue
        for dirpath, _dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in _AUDIO_EXTENSIONS:
                    continue
                full_path = os.path.join(dirpath, filename)
                try:
                    _python_scan_file(full_path, folder_path)
                    count += 1
                except Exception as e:
                    log.warning('Could not scan %s: %s', full_path, e)

    scan_status.is_scanning = False
    scan_status.count = count
    scan_status.last_scan = timezone.now()
    scan_status.save()
    log.info('Python scanner finished: %d files indexed.', count)


def _python_scan_file(path, folder_path):
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC

    audio = MutagenFile(path, easy=True)
    if audio is None:
        return

    def tag(key, default=''):
        val = audio.tags.get(key) if audio.tags else None
        return str(val[0]).strip() if val else default

    title = tag('title') or os.path.splitext(os.path.basename(path))[0]
    artist_name = tag('artist') or 'Unknown Artist'
    album_name = tag('album') or 'Unknown Album'
    genre_name = tag('genre')
    year_str = tag('date') or tag('year')
    track_str = tag('tracknumber')
    disc_str = tag('discnumber')

    year = None
    if year_str:
        try:
            year = int(year_str.split('-')[0])
        except ValueError:
            pass

    track = None
    if track_str:
        try:
            track = int(track_str.split('/')[0])
        except ValueError:
            pass

    disc = None
    if disc_str:
        try:
            disc = int(disc_str.split('/')[0])
        except ValueError:
            pass

    duration = int(audio.info.length) if hasattr(audio, 'info') and audio.info else 0
    bit_rate = int(getattr(audio.info, 'bitrate', 0) / 1000) if hasattr(audio, 'info') and audio.info else 0
    size = os.path.getsize(path)
    suffix = os.path.splitext(path)[1].lstrip('.').lower()

    data = {
        'path': path,
        'folder': folder_path,
        'title': title,
        'artist': artist_name,
        'album': album_name,
        'genre': genre_name,
        'year': year,
        'track': track,
        'disc_number': disc,
        'duration': duration,
        'bit_rate': bit_rate,
        'size': size,
        'suffix': suffix,
        'content_type': f'audio/{suffix}',
    }
    _upsert_song(data)


@api_view(['POST'])
def start_scan(request):
    err = _admin_required(request)
    if err:
        return err
    t = threading.Thread(target=_trigger_scan, daemon=True)
    t.start()
    scan = ScanStatus.get()
    return Response(ScanStatusSerializer(scan).data)


@api_view(['GET'])
def scan_status(request):
    scan = ScanStatus.get()
    return Response(ScanStatusSerializer(scan).data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def scan_callback(request):
    """
    Called by the Go scanner with results.
    Protected by shared secret header.
    """
    secret = request.headers.get('X-Scanner-Secret', '')
    if secret != settings.SCANNER_SECRET:
        return Response({'detail': 'Forbidden.'}, status=403)

    action = request.data.get('action')

    if action == 'upsert_song':
        _upsert_song(request.data)
    elif action == 'delete_song':
        Song.objects.filter(path=request.data.get('path', '')).delete()
    elif action == 'done':
        scan = ScanStatus.get()
        scan.is_scanning = False
        scan.count = request.data.get('count', scan.count)
        scan.last_scan = timezone.now()
        scan.save()

    return Response({'ok': True})


def _upsert_song(data):
    folder_path = data.get('folder')
    folder, _ = MusicFolder.objects.get_or_create(
        path=folder_path,
        defaults={'name': os.path.basename(folder_path)},
    )

    genre_name = data.get('genre', '').strip()
    genre = None
    if genre_name:
        genre, _ = Genre.objects.get_or_create(name=genre_name)

    artist_name = (data.get('artist') or 'Unknown Artist').strip()
    artist, _ = Artist.objects.get_or_create(name=artist_name)

    album_name = (data.get('album') or 'Unknown Album').strip()
    album, _ = Album.objects.get_or_create(
        name=album_name,
        artist=artist,
        defaults={'year': data.get('year'), 'genre': genre},
    )

    song, created = Song.objects.update_or_create(
        path=data['path'],
        defaults={
            'title': data.get('title') or os.path.basename(data['path']),
            'artist': artist,
            'album': album,
            'genre': genre,
            'music_folder': folder,
            'track': data.get('track'),
            'disc_number': data.get('disc_number'),
            'year': data.get('year'),
            'duration': data.get('duration', 0),
            'bit_rate': data.get('bit_rate', 0),
            'size': data.get('size', 0),
            'suffix': data.get('suffix', ''),
            'content_type': data.get('content_type', ''),
            'mb_id': data.get('mb_id', ''),
        },
    )

    # Update denormalized counts
    artist.album_count = artist.albums.count()
    artist.save(update_fields=['album_count'])
    album.song_count = album.songs.count()
    album.duration = sum(album.songs.values_list('duration', flat=True))
    if genre:
        album.genre = genre
    if not album.cover_art_path and data.get('cover_art_path'):
        album.cover_art_path = data['cover_art_path']
    album.save(update_fields=['song_count', 'duration', 'genre', 'cover_art_path'])

    # Genre counts
    if genre:
        genre.song_count = Song.objects.filter(genre=genre).count()
        genre.album_count = Album.objects.filter(genre=genre).count()
        genre.save(update_fields=['song_count', 'album_count'])

    # Update scan counter
    scan = ScanStatus.get()
    scan.count += 1
    scan.save(update_fields=['count'])


# ── Library browse (for UI) ────────────────────────────────────────────────────

@api_view(['GET'])
def artists(request):
    qs = Artist.objects.all()
    search = request.query_params.get('search')
    if search:
        qs = qs.filter(name__icontains=search)
    qs = qs.order_by('name')
    return Response(ArtistSerializer(qs, many=True).data)


@api_view(['GET'])
def artist_detail(request, artist_id):
    try:
        artist = Artist.objects.get(pk=artist_id)
    except Artist.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)
    data = ArtistSerializer(artist).data
    data['albums'] = AlbumSerializer(artist.albums.all(), many=True).data
    return Response(data)


@api_view(['GET'])
def albums(request):
    qs = Album.objects.select_related('artist', 'genre').all()
    search = request.query_params.get('search')
    if search:
        qs = qs.filter(name__icontains=search)
    sort = request.query_params.get('sort', 'name')
    if sort in ('name', '-name', 'year', '-year', 'created', '-created'):
        qs = qs.order_by(sort)
    return Response(AlbumSerializer(qs, many=True).data)


@api_view(['GET'])
def album_detail(request, album_id):
    try:
        album = Album.objects.select_related('artist', 'genre').get(pk=album_id)
    except Album.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)
    data = AlbumSerializer(album).data
    data['songs'] = SongSerializer(
        album.songs.select_related('artist', 'album', 'genre').all(),
        many=True,
    ).data
    return Response(data)


@api_view(['GET'])
def songs(request):
    qs = Song.objects.select_related('artist', 'album', 'genre').all()
    search = request.query_params.get('search')
    if search:
        qs = qs.filter(title__icontains=search)
    return Response(SongSerializer(qs[:200], many=True).data)


@api_view(['GET'])
def song_detail(request, song_id):
    try:
        song = Song.objects.select_related('artist', 'album', 'genre').get(pk=song_id)
    except Song.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)
    return Response(SongSerializer(song).data)


# ── Stats for admin dashboard ──────────────────────────────────────────────────

@api_view(['GET'])
def stats(request):
    from apps.accounts.models import User as UserModel
    return Response({
        'artists': Artist.objects.count(),
        'albums': Album.objects.count(),
        'songs': Song.objects.count(),
        'users': UserModel.objects.count(),
        'folders': MusicFolder.objects.count(),
        'genres': Genre.objects.count(),
        'playlists': Playlist.objects.count(),
    })


# ── Playlists ──────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def playlists(request):
    if request.method == 'GET':
        qs = Playlist.objects.filter(
            owner=request.user
        ) | Playlist.objects.filter(public=True)
        qs = qs.distinct().order_by('name')
        return Response(PlaylistSerializer(qs, many=True).data)

    ser = PlaylistSerializer(data={**request.data, 'owner': request.user.pk})
    if ser.is_valid():
        playlist = ser.save(owner=request.user)
        return Response(PlaylistSerializer(playlist).data, status=201)
    return Response(ser.errors, status=400)


@api_view(['GET', 'PATCH', 'DELETE'])
def playlist_detail(request, playlist_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method != 'GET':
        if playlist.owner != request.user and not request.user.is_admin_user:
            return Response({'detail': 'Forbidden.'}, status=403)

    if request.method == 'GET':
        data = PlaylistSerializer(playlist).data
        data['songs'] = SongSerializer(
            [e.song for e in playlist.entries.select_related('song__artist', 'song__album').all()],
            many=True,
        ).data
        return Response(data)

    if request.method == 'DELETE':
        playlist.delete()
        return Response(status=204)

    # PATCH
    for field in ('name', 'comment', 'public'):
        if field in request.data:
            setattr(playlist, field, request.data[field])
    playlist.save()
    return Response(PlaylistSerializer(playlist).data)


@api_view(['POST'])
def playlist_add_songs(request, playlist_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)
    if playlist.owner != request.user and not request.user.is_admin_user:
        return Response({'detail': 'Forbidden.'}, status=403)

    song_ids = request.data.get('song_ids', [])
    max_pos = playlist.entries.count()
    for i, sid in enumerate(song_ids):
        try:
            song = Song.objects.get(pk=sid)
            PlaylistSong.objects.create(playlist=playlist, song=song, position=max_pos + i)
        except Song.DoesNotExist:
            pass
    return Response({'ok': True})


# ── Internet Radio ─────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def radio_stations(request):
    if request.method == 'GET':
        return Response(RadioStationSerializer(InternetRadioStation.objects.all(), many=True).data)

    err = _admin_required(request)
    if err:
        return err
    ser = RadioStationSerializer(data=request.data)
    if ser.is_valid():
        station = ser.save()
        return Response(RadioStationSerializer(station).data, status=201)
    return Response(ser.errors, status=400)


@api_view(['PATCH', 'DELETE'])
def radio_station_detail(request, station_id):
    err = _admin_required(request)
    if err:
        return err
    try:
        station = InternetRadioStation.objects.get(pk=station_id)
    except InternetRadioStation.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method == 'DELETE':
        station.delete()
        return Response(status=204)

    ser = RadioStationSerializer(station, data=request.data, partial=True)
    if ser.is_valid():
        ser.save()
        return Response(ser.data)
    return Response(ser.errors, status=400)


@api_view(['GET'])
def cover_art_image(request, art_id: str):
    """
    Serve cover art for the web UI using JWT auth instead of Subsonic auth.
    """
    from apps.subsonic.views.media import serve_cover_art

    size = request.query_params.get('size')
    return serve_cover_art(art_id, size)


# ── Server logs ────────────────────────────────────────────────────────────────

@api_view(['GET'])
def server_logs(request):
    """Return the last N log entries from the in-memory buffer. Admin-only."""
    err = _admin_required(request)
    if err:
        return err
    try:
        limit = max(1, min(int(request.query_params.get('limit', 200)), 500))
    except (ValueError, TypeError):
        limit = 200
    with _LOG_LOCK:
        entries = list(_LOG_BUFFER)[-limit:]
    return Response({'logs': entries})
