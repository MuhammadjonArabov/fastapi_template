"""Test the AuthManager class."""

from datetime import datetime, timezone

import jwt
import pytest
from fastapi import BackgroundTasks, HTTPException, status

from settings import get_settings
from managers.auth import AuthManager, ResponseMessages
from managers.user import UserManager
from models import User
from schemas.auth import TokenRefreshRequest
from tests.helpers import get_token


@pytest.mark.unit()
class TestAuthManager:
    """Test the AuthManager class methods."""

    test_user = {
        "email": "testuser@usertest.com",
        "password": "test12345!",
        "first_name": "Test",
        "last_name": "User",
    }

    # ------------------------------------------------------------------------ #
    #                           test encoding tokens                           #
    # ------------------------------------------------------------------------ #
    def test_encode_token(self) -> None:
        """Ensure we can correctly encode a token."""
        time_now = datetime.now(tz=timezone.utc)
        token = AuthManager.encode_token(User(id=1))

        payload = jwt.decode(
            token, get_settings().secret_key, algorithms=["HS256"]
        )
        assert payload["sub"] == 1
        assert isinstance(payload["exp"], int)
        # TODO(seapagan): better comparison to ensure the exp is in the future
        # but close to the expected expiry time taking into account the setting
        # for token expiry
        assert payload["exp"] > time_now.timestamp()

    def test_encode_token_bad_data(self) -> None:
        """Test the encode_token method with bad data."""
        with pytest.raises(
            HTTPException, match=ResponseMessages.CANT_GENERATE_JWT
        ):
            AuthManager.encode_token("bad_data")  # type: ignore

    def test_encode_refresh_token(self) -> None:
        """Ensure we can correctly encode a refresh token."""
        time_now = datetime.now(tz=timezone.utc)
        refresh_token = AuthManager.encode_refresh_token(User(id=1))

        payload = jwt.decode(
            refresh_token, get_settings().secret_key, algorithms=["HS256"]
        )

        assert payload["sub"] == 1
        assert isinstance(payload["exp"], int)
        # TODO(seapagan): better comparison to ensure the exp is in the future
        # but close to the expected expiry time taking into account the expiry
        # for these is 30 days
        assert payload["exp"] > time_now.timestamp()

    def test_encode_refresh_token_bad_data(self) -> None:
        """Test the encode_refresh_token method with bad data."""
        with pytest.raises(
            HTTPException, match=ResponseMessages.CANT_GENERATE_REFRESH
        ):
            AuthManager.encode_refresh_token("bad_data")  # type: ignore



    @pytest.mark.asyncio()
    async def test_refresh_bad_token(self, test_db) -> None:
        """Test the refresh method with a bad refresh token."""
        await UserManager.register(self.test_user, test_db)
        new_token = None
        with pytest.raises(HTTPException) as exc_info:
            new_token = await AuthManager.refresh(
                TokenRefreshRequest(refresh="horrible_bad_token"), test_db
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ResponseMessages.INVALID_TOKEN
        assert new_token is None

    @pytest.mark.asyncio()
    async def test_refresh_expired_token(self, test_db, mocker) -> None:
        """Test the refresh method with an expired refresh token."""
        expired_refresh = get_token(
            sub=1,
            exp=datetime.now(tz=timezone.utc).timestamp() - 1,
            typ="refresh",
        )

        with pytest.raises(HTTPException) as exc_info:
            await AuthManager.refresh(
                TokenRefreshRequest(refresh=expired_refresh), test_db
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ResponseMessages.EXPIRED_TOKEN

    @pytest.mark.asyncio()
    async def test_refresh_wrong_token(self, test_db, mocker) -> None:
        """Test the refresh method with the wrong token 'typ'."""
        await UserManager.register(self.test_user, test_db)
        wrong_token = get_token(
            sub=1,
            exp=datetime.now(tz=timezone.utc).timestamp() + 10000,
            typ="verify",
        )

        with pytest.raises(HTTPException) as exc_info:
            await AuthManager.refresh(
                TokenRefreshRequest(refresh=wrong_token), test_db
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ResponseMessages.INVALID_TOKEN

    @pytest.mark.asyncio()
    async def test_refresh_empty_refresh_token(self, test_db) -> None:
        """Test the refresh method with no refresh token."""
        await UserManager.register(self.test_user, test_db)
        new_token = None
        with pytest.raises(HTTPException) as exc_info:
            new_token = await AuthManager.refresh(
                TokenRefreshRequest(refresh=""), test_db
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ResponseMessages.INVALID_TOKEN
        assert new_token is None

    @pytest.mark.asyncio()
    async def test_refresh_no_user(self, test_db) -> None:
        """Test the refresh method when user does not exist."""
        no_user_refresh = AuthManager.encode_refresh_token(User(id=999))
        new_token = None
        with pytest.raises(HTTPException) as exc_info:
            new_token = await AuthManager.refresh(
                TokenRefreshRequest(refresh=no_user_refresh), test_db
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ResponseMessages.USER_NOT_FOUND
        assert new_token is None

    @pytest.mark.asyncio()
    async def test_refresh_banned_user(self, test_db) -> None:
        """Test the refresh method with a banned user."""
        await UserManager.register(self.test_user, test_db)
        await UserManager.set_ban_status(1, True, 666, test_db)
        banned_user_refresh = AuthManager.encode_refresh_token(User(id=1))
        new_token = None
        with pytest.raises(HTTPException) as exc_info:
            new_token = await AuthManager.refresh(
                TokenRefreshRequest(refresh=banned_user_refresh), test_db
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ResponseMessages.INVALID_TOKEN
        assert new_token is None