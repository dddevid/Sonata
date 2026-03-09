"""scan.py — getScanStatus, startScan"""

import xml.etree.ElementTree as ET
import threading
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error
from apps.music.models import ScanStatus


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_scan_status(request):
    scan = ScanStatus.get()
    data = {
        'scanStatus': {
            'scanning': scan.is_scanning,
            'count': scan.count,
            'folderCount': scan.folder_count,
            'lastScan': scan.last_scan.isoformat() if scan.last_scan else None,
        }
    }

    def xml_builder(root):
        attrs = {
            'scanning': str(scan.is_scanning).lower(),
            'count': str(scan.count),
        }
        if scan.last_scan:
            attrs['lastScan'] = scan.last_scan.isoformat()
        ET.SubElement(root, 'scanStatus', attrs)

    return make_ok(request, data=data, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def start_scan(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    from apps.music.views import _trigger_scan
    t = threading.Thread(target=_trigger_scan, daemon=True)
    t.start()

    scan = ScanStatus.get()
    data = {
        'scanStatus': {
            'scanning': True,
            'count': scan.count,
        }
    }

    def xml_builder(root):
        ET.SubElement(root, 'scanStatus', {'scanning': 'true', 'count': str(scan.count)})

    return make_ok(request, data=data, xml_builder=xml_builder)
