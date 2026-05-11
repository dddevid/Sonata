from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'

    def ready(self):
        # Import LDAP signal handlers if LDAP is enabled
        from django.conf import settings
        if getattr(settings, 'LDAP_ENABLED', False):
            import apps.accounts.ldap_signals  # noqa: F401
