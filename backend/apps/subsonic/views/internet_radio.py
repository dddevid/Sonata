"""internet_radio.py — getInternetRadioStations, create/update/deleteInternetRadioStation"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error
from apps.music.models import InternetRadioStation


def _station_dict(s):
    return {
        'id': str(s.pk),
        'name': s.name,
        'streamUrl': s.stream_url,
        'homePageUrl': s.home_page_url,
    }


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_stations(request):
    stations = [_station_dict(s) for s in InternetRadioStation.objects.all()]

    def xml_builder(root):
        radios = ET.SubElement(root, 'internetRadioStations')
        for s in stations:
            ET.SubElement(radios, 'internetRadioStation', {k: str(v) for k, v in s.items()})

    return make_ok(request, data={'internetRadioStations': {'internetRadioStation': stations}},
                   xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def create_station(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    p = request.GET if request.method == 'GET' else request.POST
    name = p.get('name', '').strip()
    stream_url = p.get('streamUrl', '').strip()

    if not name or not stream_url:
        return make_error(request, 10, 'Required parameter missing: name or streamUrl')

    station = InternetRadioStation.objects.create(
        name=name,
        stream_url=stream_url,
        home_page_url=p.get('homepageUrl', ''),
    )
    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def update_station(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    p = request.GET if request.method == 'GET' else request.POST
    station_id = p.get('id')
    if not station_id:
        return make_error(request, 10, 'Required parameter missing: id')

    try:
        station = InternetRadioStation.objects.get(pk=station_id)
    except (InternetRadioStation.DoesNotExist, ValueError):
        return make_error(request, 70, 'Station not found')

    if 'name' in p:
        station.name = p['name']
    if 'streamUrl' in p:
        station.stream_url = p['streamUrl']
    if 'homepageUrl' in p:
        station.home_page_url = p['homepageUrl']
    station.save()

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def delete_station(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    p = request.GET if request.method == 'GET' else request.POST
    station_id = p.get('id')
    if not station_id:
        return make_error(request, 10, 'Required parameter missing: id')

    try:
        InternetRadioStation.objects.get(pk=station_id).delete()
    except (InternetRadioStation.DoesNotExist, ValueError):
        return make_error(request, 70, 'Station not found')

    return make_ok(request)
