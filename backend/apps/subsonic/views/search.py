"""search.py — search2, search3"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error, artist_to_dict, album_to_dict, song_to_dict
from apps.music.models import Artist, Album, Song, Starred


def _starred_ids(user):
    s_songs = set(Starred.objects.filter(user=user, song__isnull=False).values_list('song_id', flat=True))
    s_albums = set(Starred.objects.filter(user=user, album__isnull=False).values_list('album_id', flat=True))
    s_artists = set(Starred.objects.filter(user=user, artist__isnull=False).values_list('artist_id', flat=True))
    return s_songs, s_albums, s_artists


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def search2(request):
    return _search(request, 'searchResult2')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def search3(request):
    return _search(request, 'searchResult3')


def _search(request, tag):
    p = request.GET if request.method == 'GET' else request.POST
    query = p.get('query', '').strip()
    if not query:
        return make_ok(request, data={tag: {'artist': [], 'album': [], 'song': []}})

    artist_count = min(int(p.get('artistCount', 20)), 500)
    artist_offset = int(p.get('artistOffset', 0))
    album_count = min(int(p.get('albumCount', 20)), 500)
    album_offset = int(p.get('albumOffset', 0))
    song_count = min(int(p.get('songCount', 20)), 500)
    song_offset = int(p.get('songOffset', 0))

    s_songs, s_albums, s_artists = _starred_ids(request.subsonic_user)

    artists = Artist.objects.filter(name__icontains=query)[artist_offset:artist_offset + artist_count]
    albums = Album.objects.filter(
        Q(name__icontains=query) | Q(artist__name__icontains=query)
    ).select_related('artist', 'genre')[album_offset:album_offset + album_count]
    songs = Song.objects.filter(
        Q(title__icontains=query) | Q(artist__name__icontains=query) | Q(album__name__icontains=query)
    ).select_related('artist', 'album', 'genre')[song_offset:song_offset + song_count]

    artists_data = [artist_to_dict(a, s_artists) for a in artists]
    albums_data = [album_to_dict(al, s_albums) for al in albums]
    songs_data = [song_to_dict(s, s_songs) for s in songs]

    data = {tag: {'artist': artists_data, 'album': albums_data, 'song': songs_data}}

    def xml_builder(root):
        result = ET.SubElement(root, tag, {
            'artistCount': str(len(artists_data)),
            'albumCount': str(len(albums_data)),
            'songCount': str(len(songs_data)),
        })
        for a in artists_data:
            ET.SubElement(result, 'artist', {k: str(v) for k, v in a.items()})
        for al in albums_data:
            ET.SubElement(result, 'album', {k: str(v) for k, v in al.items()})
        for s in songs_data:
            ET.SubElement(result, 'song', {k: str(v) for k, v in s.items()})

    return make_ok(request, data=data, xml_builder=xml_builder)
