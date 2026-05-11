"""
Dynamic settings loader from database.
This module handles loading settings from the ServerSettings model
to avoid circular imports with settings.py.
"""

import os
from pathlib import Path

# Cache for settings to avoid repeated DB hits
_settings_cache = None
_cache_mtime = 0


def get_settings_file_path():
    """Get the path to a local settings file for SECRET_KEY backup."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    return data_dir / '.server_settings'


def load_secret_key_from_file():
    """Load SECRET_KEY from local file if database not available."""
    settings_file = get_settings_file_path()
    if settings_file.exists():
        content = settings_file.read_text().strip()
        if content:
            return content
    return None


def save_secret_key_to_file(secret_key):
    """Save SECRET_KEY to local file."""
    settings_file = get_settings_file_path()
    settings_file.write_text(secret_key)
    # Restrict permissions (owner read/write only)
    os.chmod(settings_file, 0o600)


def ensure_secret_key_exists():
    """
    Ensure a SECRET_KEY exists - either from file, env, or generate new.
    This is called early in settings.py before Django is fully configured.
    """
    # 1. Check environment variable first
    env_key = os.environ.get('SECRET_KEY')
    if env_key and env_key != 'dev-insecure-change-me-in-production':
        return env_key

    # 2. Check local file (for startup before DB is ready)
    file_key = load_secret_key_from_file()
    if file_key:
        return file_key

    # 3. Generate new key (will be saved to DB later)
    import secrets
    new_key = secrets.token_urlsafe(50)
    save_secret_key_to_file(new_key)
    return new_key


def get_db_settings():
    """
    Get settings from database. Called after Django is configured.
    Returns dict of settings or None if DB not ready.
    """
    global _settings_cache, _cache_mtime

    # Check if we have a cached version (works regardless of file existence)
    settings_file = get_settings_file_path()
    current_mtime = settings_file.stat().st_mtime if settings_file.exists() else 0
    if _settings_cache is not None and current_mtime == _cache_mtime:
        return _settings_cache

    try:
        from apps.accounts.models import ServerSettings
        settings_obj = ServerSettings.get()

        # If secret_key not set in DB but exists in file, import it
        if not settings_obj.secret_key:
            file_key = load_secret_key_from_file()
            if file_key:
                settings_obj.secret_key = file_key
                settings_obj.save(update_fields=['secret_key'])

        # If no subsonic encryption key, generate one
        if not settings_obj.subsonic_encryption_key:
            settings_obj.generate_subsonic_encryption_key()
            settings_obj.save(update_fields=['subsonic_encryption_key'])

        result = {
            'SECRET_KEY': settings_obj.secret_key,
            'DEBUG': settings_obj.debug,
            'SERVER_NAME': settings_obj.server_name,
            'ALLOW_SELF_REGISTER': settings_obj.allow_self_register,
            'CORS_ALLOWED_ORIGINS': settings_obj.get_cors_origins_list(),
            'ACCESS_TOKEN_LIFETIME_MINUTES': settings_obj.access_token_lifetime_minutes,
            'REFRESH_TOKEN_LIFETIME_DAYS': settings_obj.refresh_token_lifetime_days,
            'THROTTLE_USER_RATE': settings_obj.throttle_user_rate,
            'THROTTLE_ANON_RATE': settings_obj.throttle_anon_rate,
            'SUBSONIC_ENCRYPTION_KEY': settings_obj.subsonic_encryption_key,
            # LDAP settings
            'LDAP_ENABLED': settings_obj.ldap_enabled,
            'LDAP_SERVER_URI': settings_obj.ldap_server_uri,
            'LDAP_BIND_DN': settings_obj.ldap_bind_dn,
            'LDAP_BIND_PASSWORD': settings_obj.ldap_bind_password,
            'LDAP_USER_SEARCH_BASE': settings_obj.ldap_user_search_base,
            'LDAP_USER_SEARCH_FILTER': settings_obj.ldap_user_search_filter,
            'LDAP_ATTR_USERNAME': settings_obj.ldap_attr_username,
            'LDAP_ATTR_EMAIL': settings_obj.ldap_attr_email,
            'LDAP_ATTR_FIRST_NAME': settings_obj.ldap_attr_first_name,
            'LDAP_ATTR_LAST_NAME': settings_obj.ldap_attr_last_name,
            'LDAP_AUTO_CREATE_USERS': settings_obj.ldap_auto_create_users,
            'LDAP_DEFAULT_ROLE': settings_obj.ldap_default_role,
        }

        _settings_cache = result
        _cache_mtime = settings_file.stat().st_mtime if settings_file.exists() else 0
        return result

    except Exception:
        # Database not ready yet (e.g., during migrations)
        return None


def invalidate_cache():
    """Invalidate the settings cache. Call after updating settings."""
    global _settings_cache
    _settings_cache = None
    # Update file mtime to force reload
    settings_file = get_settings_file_path()
    if settings_file.exists():
        os.utime(settings_file, None)
