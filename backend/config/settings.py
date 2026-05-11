import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Dynamic Settings System ──────────────────────────────────────────────────
# Load SECRET_KEY early (from file or generate new)
from .dynamic_settings import ensure_secret_key_exists, get_db_settings
SECRET_KEY = ensure_secret_key_exists()

# Load remaining settings from database after Django is configured
_db_settings = None

def reload_settings():
    """Reload settings from database. Called by settings API endpoint."""
    global _db_settings
    from config.dynamic_settings import invalidate_cache
    invalidate_cache()
    _db_settings = get_db_settings()
    if _db_settings:
        from django.conf import settings as _s
        from datetime import timedelta
        _s.DEBUG = _db_settings.get('DEBUG', False)
        _s.SERVER_NAME = _db_settings.get('SERVER_NAME', 'Sonata')
        _s.SUBSONIC_ENCRYPTION_KEY = _db_settings.get('SUBSONIC_ENCRYPTION_KEY')
        _s.CORS_ALLOWED_ORIGINS = _db_settings.get('CORS_ALLOWED_ORIGINS', [])
        _s.CORS_ALLOW_ALL_ORIGINS = _s.DEBUG and not _s.CORS_ALLOWED_ORIGINS
        _s.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
            'user': _db_settings.get('THROTTLE_USER_RATE', '1000/day'),
            'anon': _db_settings.get('THROTTLE_ANON_RATE', '100/day'),
        }
        _s.SIMPLE_JWT.update({
            'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(_db_settings.get('ACCESS_TOKEN_LIFETIME_MINUTES', 1440))),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=int(_db_settings.get('REFRESH_TOKEN_LIFETIME_DAYS', 7))),
        })
    return _db_settings

# Try to load from DB immediately (will work after migrations)
_db_settings = get_db_settings()

# Use DB settings if available, otherwise defaults
DEBUG = _db_settings.get('DEBUG', False) if _db_settings else False
ALLOWED_HOSTS = ['*']  # Allow all hosts - CORS handles domain restrictions

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'apps.accounts',
    'apps.music',
    'apps.subsonic',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - configurable via environment or default to SQLite
_db_url = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}')
if _db_url.startswith('postgresql://') or _db_url.startswith('postgres://'):
    import re
    _m = re.match(r'postgres(?:ql)?://([^:]+):([^@]+)@([^/]+)/(.+)', _db_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'USER': _m.group(1),
            'PASSWORD': _m.group(2),
            'HOST': _m.group(3),
            'NAME': _m.group(4),
        }
    }
else:
    _sqlite_path = _db_url.replace('sqlite:///', '')
    if not os.path.isabs(_sqlite_path):
        _sqlite_path = str(BASE_DIR / _sqlite_path)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': _sqlite_path,
        }
    }

AUTH_USER_MODEL = 'accounts.User'

# ── LDAP Authentication ───────────────────────────────────────────────────────
LDAP_ENABLED = _db_settings.get('LDAP_ENABLED', False) if _db_settings else False

if LDAP_ENABLED:
    import ldap
    from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

    AUTH_LDAP_SERVER_URI = _db_settings.get('LDAP_SERVER_URI', 'ldap://localhost') if _db_settings else 'ldap://localhost'
    AUTH_LDAP_BIND_DN = _db_settings.get('LDAP_BIND_DN', '') if _db_settings else ''
    AUTH_LDAP_BIND_PASSWORD = _db_settings.get('LDAP_BIND_PASSWORD', '') if _db_settings else ''

    # User search configuration
    _ldap_search_base = _db_settings.get('LDAP_USER_SEARCH_BASE', 'ou=users,dc=example,dc=com') if _db_settings else 'ou=users,dc=example,dc=com'
    _ldap_search_filter = _db_settings.get('LDAP_USER_SEARCH_FILTER', '(uid=%(user)s)') if _db_settings else '(uid=%(user)s)'
    AUTH_LDAP_USER_SEARCH = LDAPSearch(_ldap_search_base, ldap.SCOPE_SUBTREE, _ldap_search_filter)

    # Attribute mappings
    AUTH_LDAP_USER_ATTR_MAP = {
        "username": _db_settings.get('LDAP_ATTR_USERNAME', 'uid') if _db_settings else 'uid',
        "first_name": _db_settings.get('LDAP_ATTR_FIRST_NAME', 'givenName') if _db_settings else 'givenName',
        "last_name": _db_settings.get('LDAP_ATTR_LAST_NAME', 'sn') if _db_settings else 'sn',
        "email": _db_settings.get('LDAP_ATTR_EMAIL', 'mail') if _db_settings else 'mail',
    }

    # Auto-create users and set default role
    AUTH_LDAP_ALWAYS_UPDATE_USER = True
    AUTH_LDAP_CREATE_USER = _db_settings.get('LDAP_AUTO_CREATE_USERS', True) if _db_settings else True
    LDAP_DEFAULT_ROLE = _db_settings.get('LDAP_DEFAULT_ROLE', 'user') if _db_settings else 'user'

    # Add LDAP backend to authentication backends
    AUTHENTICATION_BACKENDS = [
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
else:
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
    ]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR / 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS - loaded from database settings
# In production, specify exact origins. In debug, allow all.
if _db_settings:
    CORS_ALLOWED_ORIGINS = _db_settings.get('CORS_ALLOWED_ORIGINS', [])
    CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS
else:
    CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']
    CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Basic rate limiting to mitigate brute-force and abuse.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': _db_settings.get('THROTTLE_USER_RATE', '1000/day') if _db_settings else '1000/day',
        'anon': _db_settings.get('THROTTLE_ANON_RATE', '100/day') if _db_settings else '100/day',
    },
}

# JWT - settings loaded from database
_access_token_minutes = _db_settings.get('ACCESS_TOKEN_LIFETIME_MINUTES', 1440) if _db_settings else 1440
_refresh_token_days = _db_settings.get('REFRESH_TOKEN_LIFETIME_DAYS', 7) if _db_settings else 7

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(_access_token_minutes)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(_refresh_token_days)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# App config - loaded from database
SERVER_NAME = _db_settings.get('SERVER_NAME', 'Sonata') if _db_settings else 'Sonata'
SERVER_VERSION = '1.0.0'
SUBSONIC_API_VERSION = '1.16.1'

# Security - loaded from database (auto-generated if not set)
SUBSONIC_ENCRYPTION_KEY = _db_settings.get('SUBSONIC_ENCRYPTION_KEY') if _db_settings else None

# Upload limits — allow large audio files (default Django max is 2.5 MB in memory)
DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024         # 200 MB total request body
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024          # 10 MB per file before temp-file switch

# Folder where uploaded music files are stored (created automatically)
MUSIC_UPLOAD_ROOT = str(BASE_DIR / 'media' / 'uploads')

# Security hardening
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

