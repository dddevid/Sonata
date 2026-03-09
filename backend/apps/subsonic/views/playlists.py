"""playlists.py — getPlaylists, getPlaylist, createPlaylist, updatePlaylist, deletePlaylist"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error, song_to_dict
from apps.music.models import Playlist, PlaylistSong, Song, Starred


def _pl_dict(pl, include_songs=False, starred_ids=None):
    d = {
        'id': str(pl.pk),
        'name': pl.name,
        'comment': pl.comment,
        'owner': pl.owner.username,
        'public': str(pl.public).lower(),
        'songCount': str(pl.entries.count()),
        'duration': str(sum(e.song.duration for e in pl.entries.select_related('song').all())),
        'created': pl.created.isoformat(),
        'changed': pl.changed.isoformat(),
        'coverArt': f'pl-{pl.pk}',
    }
    if include_songs:
        d['entry'] = [
            song_to_dict(e.song, starred_ids)
            for e in pl.entries.select_related('song__artist', 'song__album', 'song__genre').all()
        ]
    return d


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_playlists(request):
    user = request.subsonic_user
    playlists = Playlist.objects.filter(Q(owner=user) | Q(public=True)).distinct().order_by('name')
    pl_list = [_pl_dict(pl) for pl in playlists]

    def xml_builder(root):
        pls = ET.SubElement(root, 'playlists')
        for pl in pl_list:
            ET.SubElement(pls, 'playlist', {k: str(v) for k, v in pl.items() if k != 'entry'})

    return make_ok(request, data={'playlists': {'playlist': pl_list}}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_playlist(request):
    p = request.GET if request.method == 'GET' else request.POST
    pl_id = p.get('id')
    if not pl_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        pl = Playlist.objects.get(pk=pl_id)
    except (Playlist.DoesNotExist, ValueError):
        return make_error(request, 70, 'Playlist not found')

    user = request.subsonic_user
    if not pl.public and pl.owner != user:
        return make_error(request, 50, 'Permission denied')

    starred_ids = set(Starred.objects.filter(user=user, song__isnull=False).values_list('song_id', flat=True))
    pl_data = _pl_dict(pl, include_songs=True, starred_ids=starred_ids)

    def xml_builder(root):
        pl_el = ET.SubElement(root, 'playlist', {k: str(v) for k, v in pl_data.items() if k != 'entry'})
        for s in pl_data.get('entry', []):
            ET.SubElement(pl_el, 'entry', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'playlist': pl_data}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def create_playlist(request):
    p = request.GET if request.method == 'GET' else request.POST
    name = p.get('name', '').strip()
    if not name:
        return make_error(request, 10, 'Required parameter missing: name')

    song_ids = p.getlist('songId') or p.getlist('songId[]')
    pl = Playlist.objects.create(name=name, owner=request.subsonic_user)
    for i, sid in enumerate(song_ids):
        try:
            song = Song.objects.get(pk=sid)
            PlaylistSong.objects.create(playlist=pl, song=song, position=i)
        except (Song.DoesNotExist, ValueError):
            pass

    pl_data = _pl_dict(pl, include_songs=True)

    def xml_builder(root):
        pl_el = ET.SubElement(root, 'playlist', {k: str(v) for k, v in pl_data.items() if k != 'entry'})

    return make_ok(request, data={'playlist': pl_data}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def update_playlist(request):
    p = request.GET if request.method == 'GET' else request.POST
    pl_id = p.get('playlistId')
    if not pl_id:
        return make_error(request, 10, 'Required parameter missing: playlistId')
    try:
        pl = Playlist.objects.get(pk=pl_id)
    except (Playlist.DoesNotExist, ValueError):
        return make_error(request, 70, 'Playlist not found')

    if pl.owner != request.subsonic_user and not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    if 'name' in p:
        pl.name = p['name']
    if 'comment' in p:
        pl.comment = p['comment']
    if 'public' in p:
        pl.public = p['public'] == 'true'
    pl.save()

    # Add songs
    add_ids = p.getlist('songIdToAdd') or p.getlist('songIdToAdd[]')
    max_pos = pl.entries.count()
    for i, sid in enumerate(add_ids):
        try:
            song = Song.objects.get(pk=sid)
            PlaylistSong.objects.create(playlist=pl, song=song, position=max_pos + i)
        except (Song.DoesNotExist, ValueError):
            pass

    # Remove songs by index
    remove_indices = [int(x) for x in (p.getlist('songIndexToRemove') or p.getlist('songIndexToRemove[]')) if x.isdigit()]
    entries = list(pl.entries.order_by('position'))
    for idx in sorted(remove_indices, reverse=True):
        if 0 <= idx < len(entries):
            entries[idx].delete()

    def xml_builder(root):
        pass

    return make_ok(request, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def delete_playlist(request):
    p = request.GET if request.method == 'GET' else request.POST
    pl_id = p.get('id')
    if not pl_id:
        return make_error(request, 10, 'Required parameter missing: id')
    try:
        pl = Playlist.objects.get(pk=pl_id)
    except (Playlist.DoesNotExist, ValueError):
        return make_error(request, 70, 'Playlist not found')

    if pl.owner != request.subsonic_user and not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    pl.delete()
    return make_ok(request)
