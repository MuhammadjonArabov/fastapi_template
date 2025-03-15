"""Set up the admin interface."""

from __future__ import annotations
from typing import TYPE_CHECKING
from app.admin.models import UserAdmin
from sqladmin import Admin
from app.admin.auth import AdminAuth
from app.settings import get_settings
from app.database.db import async_session

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI


def register_admin(app: FastAPI) -> None:
    """Register the admin views."""
    authentication_backend = AdminAuth(secret_key=get_settings().secret_key)

    if not get_settings().admin_pages_enabled:
        return

    admin = Admin(
        app,
        session_maker=async_session,
        authentication_backend=authentication_backend,
        base_url=get_settings().admin_pages_route,
        title=get_settings().admin_pages_title,
        templates_dir="app/templates/admin",
    )

    admin.add_view(UserAdmin)
