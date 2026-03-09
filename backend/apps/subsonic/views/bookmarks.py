"""bookmarks.py — getBookmarks, createBookmark, deleteBookmark, getPlayQueue, savePlayQueue"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error, song_to_dict
from apps.music.models import Bookmark, PlayQueue, PlayQueueEntry, Song, Starred


def _bookmark_dict(bm):
    d = {
        'position': str(bm.position),
        'username': bm.user.username,
        'comment': bm.comment,
        'created': bm.created.isoformat(),
        'changed': bm.changed.isoformat(),
    }
    d['entry'] = song_to_dict(bm.song)
    return d


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_bookmarks(request):
    user = request.subsonic_user
    bookmarks = Bookmark.objects.filter(user=user).select_related('song__artist', 'song__album', 'song__genre')
    bm_list = [_bookmark_dict(bm) for bm in bookmarks]

    def xml_builder(root):
        bms = ET.SubElement(root, 'bookmarks')
        for bm in bm_list:
            bm_el = ET.SubElement(bms, 'bookmark', {
                'position': bm['position'],
                'username': bm['username'],
                'comment': bm['comment'],
                'created': bm['created'],
                'changed': bm['changed'],
            })
            ET.SubElement(bm_el, 'entry', {k: str(v) for k, v in bm['entry'].items()})

    return make_ok(request, data={'bookmarks': {'bookmark': bm_list}}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def create_bookmark(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_id = p.get('id')
    position = p.get('position', '0')

    if not song_id:
        return make_error(request, 10, 'Required parameter missing: id')

    try:
        song = Song.objects.get(pk=song_id)
        Bookmark.objects.update_or_create(
            user=request.subsonic_user, song=song,
            defaults={'position': int(position), 'comment': p.get('comment', '')},
        )
    except (Song.DoesNotExist, ValueError):
        return make_error(request, 70, 'Song not found')

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def delete_bookmark(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_id = p.get('id')
    if not song_id:
        return make_error(request, 10, 'Required parameter missing: id')

    Bookmark.objects.filter(user=request.subsonic_user, song_id=song_id).delete()
    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_play_queue(request):
    user = request.subsonic_user
    try:
        queue = PlayQueue.objects.get(user=user)
    except PlayQueue.DoesNotExist:
        def xml_builder(root):
            ET.SubElement(root, 'playQueue', {'current': '', 'position': '0'})
        return make_ok(request, data={'playQueue': {'entry': [], 'current': None, 'position': 0}},
                       xml_builder=xml_builder)

    entries = queue.entries.select_related('song__artist', 'song__album', 'song__genre').all()
    songs = [song_to_dict(e.song) for e in entries]

    data = {
        'playQueue': {
            'current': str(queue.current_id) if queue.current_id else None,
            'position': queue.position,
            'changedBy': queue.changed_by,
            'changed': queue.changed.isoformat(),
            'entry': songs,
        }
    }

    def xml_builder(root):
        attrs = {'position': str(queue.position), 'changedBy': queue.changed_by}
        if queue.current_id:
            attrs['current'] = str(queue.current_id)
        pq = ET.SubElement(root, 'playQueue', attrs)
        for s in songs:
            ET.SubElement(pq, 'entry', {k: str(v) for k, v in s.items()})

    return make_ok(request, data=data, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def save_play_queue(request):
    p = request.GET if request.method == 'GET' else request.POST
    user = request.subsonic_user
    song_ids = p.getlist('id') or p.getlist('id[]')
    current_id = p.get('current')
    position = int(p.get('position', 0))
    changed_by = p.get('c', '')

    queue, _ = PlayQueue.objects.get_or_create(user=user)
    queue.entries.all().delete()

    current_song = None
    for i, sid in enumerate(song_ids):
        try:
            song = Song.objects.get(pk=sid)
            PlayQueueEntry.objects.create(queue=queue, song=song, position=i)
            if str(song.pk) == str(current_id):
                current_song = song
        except (Song.DoesNotExist, ValueError):
            pass

    queue.current = current_song
    queue.position = position
    queue.changed_by = changed_by
    queue.save()

    return make_ok(request)
