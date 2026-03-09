from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, ServerSettings
from .serializers import UserSerializer, RegisterSerializer, ChangePasswordSerializer


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Register a new user. First user becomes admin."""
    users_exist = User.objects.exists()
    if users_exist:
        settings_obj = ServerSettings.get()
        if not settings_obj.allow_self_register:
            return Response(
                {'detail': 'Self-registration is disabled by the administrator.'},
                status=status.HTTP_403_FORBIDDEN,
            )

    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = _tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            **tokens,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """Authenticate and return JWT tokens."""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'detail': 'Username and password required.'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'detail': 'Invalid credentials.'}, status=401)
    if not user.is_active:
        return Response({'detail': 'Account is disabled.'}, status=403)

    # Ensure Subsonic password is initialized for legacy users so that
    # /rest/* endpoints (including cover art) work correctly.
    if not user.subsonic_password:
        try:
            user.set_subsonic_password(password)
            user.save(update_fields=['subsonic_password'])
        except Exception:
            # If something goes wrong here, don't block normal JWT login.
            pass

    tokens = _tokens_for_user(user)
    return Response({
        'user': UserSerializer(user).data,
        **tokens,
    })


@api_view(['POST'])
def logout(request):
    """Blacklist the refresh token."""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        pass
    return Response({'detail': 'Logged out.'})


@api_view(['GET'])
def me(request):
    """Return current user info."""
    return Response(UserSerializer(request.user).data)


@api_view(['PATCH'])
def update_me(request):
    """Update current user profile."""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
def change_password(request):
    """Change current user password."""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        new_pass = serializer.validated_data['new_password']
        user.set_password(new_pass)
        user.set_subsonic_password(new_pass)
        user.save()
        tokens = _tokens_for_user(user)
        return Response({'detail': 'Password changed.', **tokens})
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def server_info(request):
    """Return server info — used by login page."""
    from django.conf import settings
    users_exist = User.objects.exists()
    allow_self_register = True
    if users_exist:
        allow_self_register = ServerSettings.get().allow_self_register
    return Response({
        'name': settings.SERVER_NAME,
        'version': settings.SERVER_VERSION,
        'users_exist': users_exist,
        'allow_self_register': allow_self_register,
    })


# --- Admin-only user management ---

def _require_admin(request):
    if not request.user.is_admin_user:
        return Response({'detail': 'Admin required.'}, status=403)
    return None


@api_view(['GET'])
def list_users(request):
    err = _require_admin(request)
    if err:
        return err
    users = User.objects.all().order_by('username')
    return Response(UserSerializer(users, many=True).data)


@api_view(['POST'])
def create_user(request):
    err = _require_admin(request)
    if err:
        return err
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Allow admin to set role
        role = request.data.get('role', 'user')
        if role == 'admin':
            user.role = User.Role.ADMIN
            user.is_staff = True
            user.save()
        return Response(UserSerializer(user).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['PATCH', 'DELETE'])
def manage_user(request, user_id):
    err = _require_admin(request)
    if err:
        return err
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method == 'DELETE':
        if user == request.user:
            return Response({'detail': 'Cannot delete yourself.'}, status=400)
        user.delete()
        return Response(status=204)

    # PATCH
    allowed = ('email', 'role', 'is_active', 'max_bit_rate',
               'stream_role', 'download_role', 'upload_role',
               'playlist_role', 'share_role', 'scrobbling_enabled')
    for field in allowed:
        if field in request.data:
            setattr(user, field, request.data[field])
    if 'password' in request.data:
        user.set_password(request.data['password'])
        user.set_subsonic_password(request.data['password'])
    if 'role' in request.data:
        user.is_staff = request.data['role'] == 'admin'
    user.save()
    return Response(UserSerializer(user).data)
