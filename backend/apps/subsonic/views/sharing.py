"""sharing.py — getShares, createShare, updateShare, deleteShare"""

import secrets
import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error, song_to_dict
from apps.music.models import Share, Song


def _share_dict(share, request):
    entries = [song_to_dict(s) for s in share.songs.all()]
    return {
        'id': str(share.pk),
        'url': request.build_absolute_uri(f'/share/{share.url_token}'),
        'description': share.description,
        'username': share.user.username,
        'created': share.created.isoformat(),
        'expires': share.expires.isoformat() if share.expires else '',
        'lastVisited': share.last_visited.isoformat() if share.last_visited else '',
        'visitCount': str(share.visit_count),
        'entry': entries,
    }


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_shares(request):
    user = request.subsonic_user
    shares = Share.objects.filter(user=user).prefetch_related('songs__artist', 'songs__album')
    shares_list = [_share_dict(s, request) for s in shares]

    def xml_builder(root):
        shares_el = ET.SubElement(root, 'shares')
        for sh in shares_list:
            sh_el = ET.SubElement(shares_el, 'share', {
                k: str(v) for k, v in sh.items() if k != 'entry'
            })
            for s in sh['entry']:
                ET.SubElement(sh_el, 'entry', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'shares': {'share': shares_list}}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def create_share(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_ids = p.getlist('id') or p.getlist('id[]')
    description = p.get('description', '')

    share = Share.objects.create(
        user=request.subsonic_user,
        description=description,
        url_token=secrets.token_urlsafe(16),
    )
    for sid in song_ids:
        try:
            share.songs.add(Song.objects.get(pk=sid))
        except (Song.DoesNotExist, ValueError):
            pass

    sh_dict = _share_dict(share, request)

    def xml_builder(root):
        shares_el = ET.SubElement(root, 'shares')
        sh_el = ET.SubElement(shares_el, 'share', {
            k: str(v) for k, v in sh_dict.items() if k != 'entry'
        })
        for s in sh_dict['entry']:
            ET.SubElement(sh_el, 'entry', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'shares': {'share': [sh_dict]}}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def update_share(request):
    p = request.GET if request.method == 'GET' else request.POST
    share_id = p.get('id')
    if not share_id:
        return make_error(request, 10, 'Required parameter missing: id')

    try:
        share = Share.objects.get(pk=share_id, user=request.subsonic_user)
    except (Share.DoesNotExist, ValueError):
        return make_error(request, 70, 'Share not found')

    if 'description' in p:
        share.description = p['description']
    if 'expires' in p and p['expires']:
        from django.utils.dateparse import parse_datetime
        share.expires = parse_datetime(p['expires'])
    share.save()

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def delete_share(request):
    p = request.GET if request.method == 'GET' else request.POST
    share_id = p.get('id')
    if not share_id:
        return make_error(request, 10, 'Required parameter missing: id')

    Share.objects.filter(pk=share_id, user=request.subsonic_user).delete()
    return make_ok(request)
