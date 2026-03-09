"""lists.py — getAlbumList, getAlbumList2, getRandomSongs, getSongsByGenre, getNowPlaying, getStarred, getStarred2"""

import xml.etree.ElementTree as ET
import random
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error, album_to_dict, song_to_dict
from apps.music.models import Album, Song, Genre, Starred, ActiveStream
from datetime import timedelta
from django.utils import timezone


def _starred_song_ids(user):
    return set(Starred.objects.filter(user=user, song__isnull=False).values_list('song_id', flat=True))


def _starred_album_ids(user):
    return set(Starred.objects.filter(user=user, album__isnull=False).values_list('album_id', flat=True))


def _parse_list_params(p):
    size = min(int(p.get('size', 10)), 500)
    offset = int(p.get('offset', 0))
    return size, offset


# ── getAlbumList ───────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_album_list(request):
    return _album_list(request, 'albumList')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_album_list2(request):
    return _album_list(request, 'albumList2')


def _album_list(request, tag):
    p = request.GET if request.method == 'GET' else request.POST
    list_type = p.get('type', 'alphabeticalByName')
    size, offset = _parse_list_params(p)
    starred_ids = _starred_album_ids(request.subsonic_user)

    qs = Album.objects.select_related('artist', 'genre').all()

    if list_type == 'random':
        # For random selection, rely on database-level random ordering
        # and avoid loading all primary keys into memory.
        qs = qs.order_by('?')[offset:offset + size]
    elif list_type == 'newest':
        qs = qs.order_by('-created')[offset:offset + size]
    elif list_type == 'alphabeticalByName':
        qs = qs.order_by('name')[offset:offset + size]
    elif list_type == 'alphabeticalByArtist':
        qs = qs.order_by('artist__name', 'name')[offset:offset + size]
    elif list_type == 'byYear':
        from_year = int(p.get('fromYear', 0))
        to_year = int(p.get('toYear', 9999))
        order = 'year' if from_year <= to_year else '-year'
        qs = qs.filter(year__gte=min(from_year, to_year), year__lte=max(from_year, to_year)).order_by(order)[offset:offset + size]
    elif list_type == 'byGenre':
        genre_name = p.get('genre', '')
        qs = qs.filter(genre__name=genre_name).order_by('name')[offset:offset + size]
    elif list_type == 'frequent':
        qs = qs.order_by('-songs__play_count').distinct()[offset:offset + size]
    elif list_type == 'recent':
        qs = qs.order_by('-songs__last_played').distinct()[offset:offset + size]
    elif list_type == 'starred':
        qs = qs.filter(pk__in=starred_ids)[offset:offset + size]
    else:
        qs = qs.order_by('name')[offset:offset + size]

    albums = [album_to_dict(al, starred_ids) for al in qs]

    def xml_builder(root):
        al_root = ET.SubElement(root, tag)
        for al in albums:
            ET.SubElement(al_root, 'album', {k: str(v) for k, v in al.items()})

    return make_ok(request, data={tag: {'album': albums}}, xml_builder=xml_builder)


# ── getRandomSongs ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_random_songs(request):
    p = request.GET if request.method == 'GET' else request.POST
    size = min(int(p.get('size', 10)), 500)
    genre_name = p.get('genre')
    from_year = p.get('fromYear')
    to_year = p.get('toYear')

    qs = Song.objects.select_related('artist', 'album', 'genre').all()
    if genre_name:
        qs = qs.filter(genre__name=genre_name)
    if from_year:
        qs = qs.filter(year__gte=int(from_year))
    if to_year:
        qs = qs.filter(year__lte=int(to_year))

    # Use database-level random ordering instead of shuffling all PKs in memory.
    songs_qs = qs.order_by('?')[:size]

    starred_ids = _starred_song_ids(request.subsonic_user)
    songs = [song_to_dict(s, starred_ids) for s in songs_qs]

    def xml_builder(root):
        songs_el = ET.SubElement(root, 'randomSongs')
        for s in songs:
            ET.SubElement(songs_el, 'song', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'randomSongs': {'song': songs}}, xml_builder=xml_builder)


# ── getSongsByGenre ────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_songs_by_genre(request):
    p = request.GET if request.method == 'GET' else request.POST
    genre_name = p.get('genre', '')
    size, offset = _parse_list_params(p)

    qs = Song.objects.filter(genre__name=genre_name).select_related('artist', 'album', 'genre')[offset:offset + size]
    starred_ids = _starred_song_ids(request.subsonic_user)
    songs = [song_to_dict(s, starred_ids) for s in qs]

    def xml_builder(root):
        el = ET.SubElement(root, 'songsByGenre')
        for s in songs:
            ET.SubElement(el, 'song', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'songsByGenre': {'song': songs}}, xml_builder=xml_builder)


# ── getNowPlaying ──────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_now_playing(request):
    threshold = timezone.now() - timedelta(minutes=15)
    qs = ActiveStream.objects.filter(last_seen__gte=threshold).select_related('song__artist', 'song__album', 'user')

    entries = []
    for active in qs:
        mins_ago = int((timezone.now() - active.last_seen).total_seconds() / 60)
        entry = song_to_dict(active.song)
        entry['username'] = active.user.username
        entry['minutesAgo'] = str(mins_ago)
        entry['playerId'] = active.client
        entries.append(entry)

    def xml_builder(root):
        el = ET.SubElement(root, 'nowPlaying')
        for e in entries:
            ET.SubElement(el, 'entry', {k: str(v) for k, v in e.items()})

    return make_ok(request, data={'nowPlaying': {'entry': entries}}, xml_builder=xml_builder)


# ── getStarred / getStarred2 ───────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_starred(request):
    return _starred_response(request, 'starred')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_starred2(request):
    return _starred_response(request, 'starred2')


def _starred_response(request, tag):
    user = request.subsonic_user
    starred_songs = Starred.objects.filter(user=user, song__isnull=False).select_related('song__artist', 'song__album', 'song__genre')
    starred_albums = Starred.objects.filter(user=user, album__isnull=False).select_related('album__artist', 'album__genre')
    starred_artists = Starred.objects.filter(user=user, artist__isnull=False).select_related('artist')

    s_song_ids = {s.song_id for s in starred_songs}
    s_album_ids = {s.album_id for s in starred_albums}
    s_artist_ids = {s.artist_id for s in starred_artists}

    songs = [song_to_dict(s.song, s_song_ids) for s in starred_songs]
    albums = [album_to_dict(s.album, s_album_ids) for s in starred_albums]
    artists = []
    for s in starred_artists:
        from apps.subsonic.helpers import artist_to_dict
        artists.append(artist_to_dict(s.artist, s_artist_ids))

    data = {tag: {'song': songs, 'album': albums, 'artist': artists}}

    def xml_builder(root):
        starred_el = ET.SubElement(root, tag)
        for a in artists:
            ET.SubElement(starred_el, 'artist', {k: str(v) for k, v in a.items()})
        for al in albums:
            ET.SubElement(starred_el, 'album', {k: str(v) for k, v in al.items()})
        for s in songs:
            ET.SubElement(starred_el, 'song', {k: str(v) for k, v in s.items()})

    return make_ok(request, data=data, xml_builder=xml_builder)
