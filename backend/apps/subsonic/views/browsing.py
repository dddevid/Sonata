"""browsing.py — getMusicFolders, getIndexes, getArtists, getArtist, getAlbum, getSong, getGenres …"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import (
    make_ok, make_error,
    artist_to_dict, album_to_dict, song_to_dict,
)
from apps.music.models import MusicFolder, Artist, Album, Song, Genre, Starred
from apps.music.metadata import download_artist_image


def _starred_song_ids(user):
    return set(Starred.objects.filter(user=user, song__isnull=False)
               .values_list('song_id', flat=True))


def _starred_album_ids(user):
    return set(Starred.objects.filter(user=user, album__isnull=False)
               .values_list('album_id', flat=True))


def _starred_artist_ids(user):
    return set(Starred.objects.filter(user=user, artist__isnull=False)
               .values_list('artist_id', flat=True))


# ── getMusicFolders ────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_music_folders(request):
    folders = list(MusicFolder.objects.filter(enabled=True))

    def xml_builder(root):
        mf = ET.SubElement(root, 'musicFolders')
        for f in folders:
            ET.SubElement(mf, 'musicFolder', {'id': str(f.pk), 'name': f.name})

    return make_ok(request, data={
        'musicFolders': {
            'musicFolder': [{'id': f.pk, 'name': f.name} for f in folders]
        }
    }, xml_builder=xml_builder)


# ── getIndexes ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_indexes(request):
    """Folder/artist index grouped by first letter."""
    p = request.GET if request.method == 'GET' else request.POST
    music_folder_id = p.get('musicFolderId')

    qs = Artist.objects.all()
    if music_folder_id:
        qs = qs.filter(songs__music_folder_id=music_folder_id).distinct()

    starred_ids = _starred_artist_ids(request.subsonic_user)
    index_map = defaultdict(list)

    for artist in qs.order_by('name'):
        letter = artist.name[0].upper() if artist.name else '#'
        if not letter.isalpha():
            letter = '#'
        index_map[letter].append(artist_to_dict(artist, starred_ids))

    indexes_list = []
    for letter in sorted(index_map.keys()):
        indexes_list.append({'name': letter, 'artist': index_map[letter]})

    def xml_builder(root):
        idx_root = ET.SubElement(root, 'indexes', {
            'lastModified': '0', 'ignoredArticles': 'The El La Los Las'
        })
        for idx in indexes_list:
            idx_el = ET.SubElement(idx_root, 'index', {'name': idx['name']})
            for a in idx['artist']:
                ET.SubElement(idx_el, 'artist', {k: str(v) for k, v in a.items()})

    return make_ok(request, data={
        'indexes': {'lastModified': 0, 'ignoredArticles': 'The El La Los Las', 'index': indexes_list}
    }, xml_builder=xml_builder)


# ── getArtists (ID3) ───────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_artists(request):
    starred_ids = _starred_artist_ids(request.subsonic_user)
    index_map = defaultdict(list)

    for artist in Artist.objects.all().order_by('name'):
        letter = artist.name[0].upper() if artist.name else '#'
        if not letter.isalpha():
            letter = '#'
        index_map[letter].append(artist_to_dict(artist, starred_ids))

    indexes_list = [
        {'name': l, 'artist': index_map[l]}
        for l in sorted(index_map.keys())
    ]

    def xml_builder(root):
        artists_el = ET.SubElement(root, 'artists', {'ignoredArticles': 'The El La Los Las'})
        for idx in indexes_list:
            idx_el = ET.SubElement(artists_el, 'index', {'name': idx['name']})
            for a in idx['artist']:
                ET.SubElement(idx_el, 'artist', {k: str(v) for k, v in a.items()})

    return make_ok(request, data={
        'artists': {'ignoredArticles': 'The El La Los Las', 'index': indexes_list}
    }, xml_builder=xml_builder)


# ── getArtist ──────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_artist(request):
    p = request.GET if request.method == 'GET' else request.POST
    artist_id = p.get('id')
    if not artist_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        artist = Artist.objects.get(pk=artist_id)
    except (Artist.DoesNotExist, ValueError):
        return make_error(request, 70, 'Artist not found')

    if not artist.image_path and artist.name != 'Unknown Artist':
        download_artist_image(artist)

    starred_artist_ids = _starred_artist_ids(request.subsonic_user)
    starred_album_ids = _starred_album_ids(request.subsonic_user)

    a_dict = artist_to_dict(artist, starred_artist_ids)
    albums = [album_to_dict(al, starred_album_ids) for al in artist.albums.all().order_by('year', 'name')]
    a_dict['album'] = albums

    def xml_builder(root):
        a_el = ET.SubElement(root, 'artist', {k: str(v) for k, v in {
            **artist_to_dict(artist, starred_artist_ids),
            'albumCount': str(len(albums)),
        }.items()})
        for al in albums:
            ET.SubElement(a_el, 'album', {k: str(v) for k, v in al.items()})

    return make_ok(request, data={'artist': a_dict}, xml_builder=xml_builder)


# ── getAlbum ───────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_album(request):
    p = request.GET if request.method == 'GET' else request.POST
    album_id = p.get('id')
    if not album_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        album = Album.objects.select_related('artist', 'genre').get(pk=album_id)
    except (Album.DoesNotExist, ValueError):
        return make_error(request, 70, 'Album not found')

    starred_song_ids = _starred_song_ids(request.subsonic_user)
    starred_album_ids = _starred_album_ids(request.subsonic_user)

    al_dict = album_to_dict(album, starred_album_ids)
    songs = [
        song_to_dict(s, starred_song_ids)
        for s in album.songs.select_related('artist', 'album', 'genre').order_by('disc_number', 'track')
    ]
    al_dict['song'] = songs

    def xml_builder(root):
        al_el = ET.SubElement(root, 'album', {k: str(v) for k, v in album_to_dict(album, starred_album_ids).items()})
        for s in songs:
            ET.SubElement(al_el, 'song', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'album': al_dict}, xml_builder=xml_builder)


# ── getSong ────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_song(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_id = p.get('id')
    if not song_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        song = Song.objects.select_related('artist', 'album', 'genre').get(pk=song_id)
    except (Song.DoesNotExist, ValueError):
        return make_error(request, 70, 'Song not found')

    starred_ids = _starred_song_ids(request.subsonic_user)
    s_dict = song_to_dict(song, starred_ids)

    def xml_builder(root):
        ET.SubElement(root, 'song', {k: str(v) for k, v in s_dict.items()})

    return make_ok(request, data={'song': s_dict}, xml_builder=xml_builder)


# ── getMusicDirectory ──────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_music_directory(request):
    """Folder-based browsing. We map artists and albums to directory entries."""
    p = request.GET if request.method == 'GET' else request.POST
    dir_id = p.get('id', '')
    if not dir_id:
        return make_error(request, 10, 'Required parameter missing: id')

    starred_album_ids = _starred_album_ids(request.subsonic_user)
    starred_song_ids = _starred_song_ids(request.subsonic_user)

    # If id starts with 'ar-' → artist directory → list albums
    if dir_id.startswith('ar-'):
        artist_id = dir_id[3:]
        try:
            artist = Artist.objects.get(pk=artist_id)
        except (Artist.DoesNotExist, ValueError):
            return make_error(request, 70, 'Directory not found')
        children = [album_to_dict(al, starred_album_ids) for al in artist.albums.all().order_by('year')]
        dir_dict = {'id': dir_id, 'name': artist.name, 'child': children}
    # If id starts with 'al-' → album directory → list songs
    elif dir_id.startswith('al-'):
        album_id = dir_id[3:]
        try:
            album = Album.objects.select_related('artist').get(pk=album_id)
        except (Album.DoesNotExist, ValueError):
            return make_error(request, 70, 'Directory not found')
        children = [song_to_dict(s, starred_song_ids) for s in album.songs.select_related('artist', 'album', 'genre').all()]
        dir_dict = {'id': dir_id, 'name': album.name, 'parent': f'ar-{album.artist_id}', 'child': children}
    else:
        # Treat as music folder → list artists
        try:
            folder = MusicFolder.objects.get(pk=dir_id)
        except (MusicFolder.DoesNotExist, ValueError):
            return make_error(request, 70, 'Directory not found')
        artists = Artist.objects.filter(songs__music_folder=folder).distinct().order_by('name')
        children = [{'id': f'ar-{a.pk}', 'title': a.name, 'isDir': True} for a in artists]
        dir_dict = {'id': dir_id, 'name': folder.name, 'child': children}

    def xml_builder(root):
        dir_el = ET.SubElement(root, 'directory', {'id': dir_dict['id'], 'name': dir_dict['name']})
        for child in dir_dict.get('child', []):
            ET.SubElement(dir_el, 'child', {k: str(v) for k, v in child.items()})

    return make_ok(request, data={'directory': dir_dict}, xml_builder=xml_builder)


# ── getGenres ──────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_genres(request):
    genres = Genre.objects.all().order_by('name')
    g_list = [{'value': g.name, 'songCount': g.song_count, 'albumCount': g.album_count} for g in genres]

    def xml_builder(root):
        genres_el = ET.SubElement(root, 'genres')
        for g in g_list:
            el = ET.SubElement(genres_el, 'genre', {
                'songCount': str(g['songCount']),
                'albumCount': str(g['albumCount']),
            })
            el.text = g['value']

    return make_ok(request, data={'genres': {'genre': g_list}}, xml_builder=xml_builder)


# ── getArtistInfo / getArtistInfo2 ─────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_artist_info(request):
    p = request.GET if request.method == 'GET' else request.POST
    artist_id = p.get('id')
    if not artist_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        artist = Artist.objects.get(pk=artist_id)
    except (Artist.DoesNotExist, ValueError):
        return make_error(request, 70, 'Artist not found')
    info = {
        'biography': artist.biography,
        'musicBrainzId': artist.mb_id,
        'artistImageUrl': artist.image_url,
        'similarArtist': [],
    }

    def xml_builder(root):
        el = ET.SubElement(root, 'artistInfo')
        ET.SubElement(el, 'biography').text = info['biography']
        ET.SubElement(el, 'musicBrainzId').text = info['musicBrainzId']
        ET.SubElement(el, 'artistImageUrl').text = info['artistImageUrl']

    return make_ok(request, data={'artistInfo': info}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_artist_info2(request):
    return get_artist_info(request)


# ── getAlbumInfo / getAlbumInfo2 ───────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_album_info(request):
    p = request.GET if request.method == 'GET' else request.POST
    album_id = p.get('id')
    if not album_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        album = Album.objects.get(pk=album_id)
    except (Album.DoesNotExist, ValueError):
        return make_error(request, 70, 'Album not found')
    info = {'notes': '', 'musicBrainzId': album.mb_id, 'lastFmUrl': ''}

    def xml_builder(root):
        el = ET.SubElement(root, 'albumInfo')
        ET.SubElement(el, 'notes').text = info['notes']
        ET.SubElement(el, 'musicBrainzId').text = info['musicBrainzId']

    return make_ok(request, data={'albumInfo': info}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_album_info2(request):
    return get_album_info(request)


# ── getSimilarSongs, getTopSongs (stub) ────────────────────────────────────────

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_similar_songs(request):
    def xml_builder(root):
        ET.SubElement(root, 'similarSongs')
    return make_ok(request, data={'similarSongs': {'song': []}}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_similar_songs2(request):
    return get_similar_songs(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_top_songs(request):
    def xml_builder(root):
        ET.SubElement(root, 'topSongs')
    return make_ok(request, data={'topSongs': {'song': []}}, xml_builder=xml_builder)
