"""system.py — ping, getLicense, getOpenSubsonicExtensions"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def ping(request):
    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_license(request):
    data = {
        'license': {
            'valid': True,
            'email': 'sonata@localhost',
            'licenseExpires': '2099-01-01T00:00:00.000Z',
        }
    }

    def xml_builder(root):
        ET.SubElement(root, 'license', {
            'valid': 'true',
            'email': 'sonata@localhost',
            'licenseExpires': '2099-01-01T00:00:00.000Z',
        })

    return make_ok(request, data=data, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_extensions(request):
    extensions = [
        {'name': 'template', 'versions': [1]},
        {'name': 'transcodeOffset', 'versions': [1]},
        {'name': 'formPost', 'versions': [1]},
        {'name': 'saveQueue', 'versions': [1]},
    ]

    def xml_builder(root):
        ext_root = ET.SubElement(root, 'openSubsonicExtensions')
        for ext in extensions:
            e = ET.SubElement(ext_root, 'extension', {'name': ext['name']})
            for v in ext['versions']:
                ET.SubElement(e, 'version').text = str(v)

    return make_ok(request, data={'openSubsonicExtensions': extensions}, xml_builder=xml_builder)
