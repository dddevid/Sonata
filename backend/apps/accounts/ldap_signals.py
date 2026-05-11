"""
Signal handlers for LDAP authentication.
Sets default role and subsonic password for LDAP-created users.
"""

from django.dispatch import receiver
from django.conf import settings
from django_auth_ldap.backend import populate_user
import logging

logger = logging.getLogger(__name__)


@receiver(populate_user)
def ldap_user_populate(sender, user, ldap_user, **kwargs):
    """
    Called when a user is populated from LDAP.
    Sets the default role from settings.
    """
    from .models import User

    # Set default role if LDAP_DEFAULT_ROLE is configured
    ldap_default_role = getattr(settings, 'LDAP_DEFAULT_ROLE', 'user')
    if ldap_default_role == 'admin':
        user.role = User.Role.ADMIN
        user.is_staff = True
    else:
        user.role = User.Role.USER

    # Mark as LDAP user (optional - could add a field later)
    logger.info(f"LDAP user populated: {user.username} with role {user.role}")

    # Note: We can't set subsonic_password here because we don't have
    # the raw password. The user will need to set it via the UI or
    # we'll use a default approach in the login view.
