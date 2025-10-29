# orders/utils.py
from __future__ import annotations

from typing import Optional

from .models import AppUser
from . import services


def get_or_create_app_user(dj_user) -> Optional[AppUser]:
    """
    Back-compat wrapper.
    For an authenticated Django user, upsert/fetch the mapped AppUser row.
    Returns None if the user is anonymous or has no email.
    """
    return services.ensure_app_user_for_django_user(dj_user)


def get_guest_app_user() -> AppUser:
    """
    Back-compat wrapper.
    Return (and create if needed) the single reusable Guest AppUser.
    """
    return services.get_guest_app_user()


def resolve_app_user(dj_user) -> AppUser:
    """
    Convenience helper: return an AppUser for the current request user,
    falling back to the Guest AppUser for anonymous sessions.
    """
    # services._resolve_app_user is internal; call the public pieces explicitly
    app_user = services.ensure_app_user_for_django_user(dj_user)
    return app_user or services.get_guest_app_user()
