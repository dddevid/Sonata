"""
Subsonic API authentication decorator.

Supports:
  1. Token auth:  u=<user>&t=<md5(password+salt)>&s=<salt>
  2. Password:    u=<user>&p=<plaintext>
  3. Hex password: u=<user>&p=enc:<hex>
"""

import hashlib
from functools import wraps
from apps.accounts.models import User
from .helpers import make_error


def subsonic_auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        p = request.GET if request.method == 'GET' else request.POST

        # 1. Fallback for Web UI: JWT in query params
        jwt_token = p.get('jwt')
        if jwt_token:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            try:
                validated_token = JWTAuthentication().get_validated_token(jwt_token)
                user = JWTAuthentication().get_user(validated_token)
                request.subsonic_user = user
                return view_func(request, *args, **kwargs)
            except Exception:
                return make_error(request, 40, 'Invalid JWT token')

        # 2. Standard Subsonic Auth
        username = p.get('u', '').strip()
        if not username:
            return make_error(request, 10, 'Required parameter missing: u')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return make_error(request, 40, 'Wrong username or password')

        if not user.is_active:
            return make_error(request, 40, 'User is disabled')

        token = p.get('t', '')
        salt = p.get('s', '')
        password = p.get('p', '')

        subsonic_password = user.get_subsonic_password()

        if token and salt:
            # Token-based authentication
            expected = hashlib.md5(
                f'{subsonic_password}{salt}'.encode()
            ).hexdigest()
            if token != expected:
                return make_error(request, 40, 'Wrong username or password')
        elif password:
            # Plain-text or hex-encoded password
            if password.startswith('enc:'):
                try:
                    password = bytes.fromhex(password[4:]).decode('utf-8')
                except (ValueError, UnicodeDecodeError):
                    return make_error(request, 40, 'Wrong username or password')
            if password != subsonic_password:
                return make_error(request, 40, 'Wrong username or password')
        else:
            return make_error(request, 10, 'Required parameter missing: p or t/s')

        # Attach user to request for downstream use
        request.subsonic_user = user
        return view_func(request, *args, **kwargs)

    return wrapper
