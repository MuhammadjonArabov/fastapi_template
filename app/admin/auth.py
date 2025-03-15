"""Handle the authentication for the admin interface."""

from __future__ import annotations
import json
import re
from typing import TYPE_CHECKING, Any

from cryptography.fernet import Fernet, InvalidToken
from sqladmin.authentication import AuthenticationBackend

from app.settings import get_settings
from app.database.db import async_session
from app.database.helpers import (
    get_user_by_phone_,
    get_user_by_id_,
    verify_password,
)
from app.logs import logger
from app.models.enums import RoleType

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import Request
    from app.models.users import User


class AdminAuth(AuthenticationBackend):
    """Setup the authentication backend for the admin interface."""

    def __init__(self, secret_key: str) -> None:
        """Initialize the auth backend with encryption key."""
        super().__init__(secret_key)
        self.fernet = Fernet(get_settings().admin_pages_encryption_key.encode())
        self._timeout = get_settings().admin_pages_timeout

    def _create_token(self, user_id: int) -> str:
        """Create an encrypted token containing user data."""
        token_data = {"user_id": user_id}
        return self.fernet.encrypt(json.dumps(token_data).encode()).decode()

    def _decode_token(self, token: str) -> dict[str, Any] | None:
        """Decode and validate the token."""
        try:
            decoded = self.fernet.decrypt(
                token.encode(), ttl=self._timeout
            ).decode()
            data: dict[str, Any] = json.loads(decoded)
        except (json.JSONDecodeError, InvalidToken, UnicodeError):
            return None
        else:
            return data

    async def login(self, request: Request) -> bool:
        """Login the user with phone and password."""
        form = await request.form()
        phone = form.get("username")  # sqladmin uses 'username' as field name
        password = form.get("password")

        if not phone or not password:
            return False

        pattern = r"^\+998\d{9}$"
        if not re.match(pattern, phone):
            logger.error("Invalid phone number format! Use: +998xxxxxxxxx")
            return False

        async with async_session() as db:
            user = await get_user_by_phone_(phone, db)

            if not user or not self._validate_user(password, user):
                logger.error("Failed admin site login attempt by %s", phone)
                return False

            token = self._create_token(user.id)
            request.session.update({"token": token})
            return True

    def _validate_user(self, password: str, user: User | None) -> bool:
        """Validate if the user can access admin interface."""
        return not (
                not user
                or not verify_password(password, user.password)
                or user.role != RoleType.admin
                or user.banned
        )

    async def logout(self, request: Request) -> bool:
        """Logout the user."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Authenticate using the encrypted token."""
        token = request.session.get("token")

        if not token:
            logger.error("No token found in session")
            return False

        token_data = self._decode_token(token)
        if not token_data:
            request.session.clear()
            return False

        async with async_session() as db:
            user = await get_user_by_id_(token_data["user_id"], db)

            if not user or user.role != RoleType.admin or user.banned:
                request.session.clear()
                return False

            return True
