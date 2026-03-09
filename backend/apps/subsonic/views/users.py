"""users.py — getUser, getUsers, createUser, updateUser, changePassword, deleteUser"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error
from apps.accounts.models import User


def _user_dict(user):
    return {
        'username': user.username,
        'email': user.email,
        'scrobblingEnabled': str(user.scrobbling_enabled).lower(),
        'maxBitRate': str(user.max_bit_rate),
        'adminRole': str(user.is_admin_user).lower(),
        'settingsRole': str(user.is_admin_user).lower(),
        'downloadRole': str(user.download_role).lower(),
        'uploadRole': str(user.upload_role).lower(),
        'playlistRole': str(user.playlist_role).lower(),
        'coverArtRole': str(user.cover_art_role).lower(),
        'commentRole': str(user.comment_role).lower(),
        'podcastRole': str(user.podcast_role).lower(),
        'streamRole': str(user.stream_role).lower(),
        'jukeboxRole': str(user.jukebox_role).lower(),
        'shareRole': str(user.share_role).lower(),
        'videoConversionRole': str(user.video_conversion_role).lower(),
    }


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_user(request):
    p = request.GET if request.method == 'GET' else request.POST
    username = p.get('username', request.subsonic_user.username)

    if username != request.subsonic_user.username and not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return make_error(request, 70, 'User not found')

    u_dict = _user_dict(user)

    def xml_builder(root):
        ET.SubElement(root, 'user', {k: str(v) for k, v in u_dict.items()})

    return make_ok(request, data={'user': u_dict}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def get_users(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    users = User.objects.filter(is_active=True)
    u_list = [_user_dict(u) for u in users]

    def xml_builder(root):
        users_el = ET.SubElement(root, 'users')
        for u in u_list:
            ET.SubElement(users_el, 'user', {k: str(v) for k, v in u.items()})

    return make_ok(request, data={'users': {'user': u_list}}, xml_builder=xml_builder)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def create_user(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    p = request.GET if request.method == 'GET' else request.POST
    username = p.get('username', '').strip()
    password = p.get('password', '')
    email = p.get('email', '')

    if not username or not password:
        return make_error(request, 10, 'Required parameter missing: username or password')
    if User.objects.filter(username=username).exists():
        return make_error(request, 0, 'Username already exists')

    user = User(username=username, email=email)
    user.set_password(password)
    # Store Subsonic password using the model helper (encryption-aware)
    user.set_subsonic_password(password)
    user.admin_role = p.get('adminRole', 'false').lower() == 'true'
    if user.admin_role:
        user.role = User.Role.ADMIN
        user.is_staff = True
    user.save()

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def update_user(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    p = request.GET if request.method == 'GET' else request.POST
    username = p.get('username', '').strip()
    if not username:
        return make_error(request, 10, 'Required parameter missing: username')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return make_error(request, 70, 'User not found')

    if 'password' in p:
        user.set_password(p['password'])
        user.set_subsonic_password(p['password'])
    if 'email' in p:
        user.email = p['email']
    if 'maxBitRate' in p:
        user.max_bit_rate = int(p['maxBitRate'])
    if 'adminRole' in p:
        is_admin = p['adminRole'].lower() == 'true'
        user.role = User.Role.ADMIN if is_admin else User.Role.USER
        user.is_staff = is_admin
    user.save()

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def change_password(request):
    p = request.GET if request.method == 'GET' else request.POST
    username = p.get('username', '').strip()
    password = p.get('password', '')

    if not username or not password:
        return make_error(request, 10, 'Required parameter missing')

    if username != request.subsonic_user.username and not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    if password.startswith('enc:'):
        try:
            password = bytes.fromhex(password[4:]).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            return make_error(request, 10, 'Invalid encoded password')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return make_error(request, 70, 'User not found')

    user.set_password(password)
    user.set_subsonic_password(password)
    user.save()

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def delete_user(request):
    if not request.subsonic_user.is_admin_user:
        return make_error(request, 50, 'Permission denied')

    p = request.GET if request.method == 'GET' else request.POST
    username = p.get('username', '').strip()
    if not username:
        return make_error(request, 10, 'Required parameter missing: username')

    if username == request.subsonic_user.username:
        return make_error(request, 0, 'Cannot delete yourself')

    try:
        user = User.objects.get(username=username)
        user.delete()
    except User.DoesNotExist:
        return make_error(request, 70, 'User not found')

    return make_ok(request)
