"""Test the authentication routes of the application."""

import logging
from typing import Union

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.managers.auth import AuthManager
from app.managers.user import ErrorMessages as UserErrorMessages
from app.managers.user import pwd_context
from app.models.enums import RoleType
from app.models.users import User

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


@pytest.mark.integration()
class TestAuthRoutes:
    """Test the authentication routes of the application."""

    # ------------------------------------------------------------------------ #
    #        some constants to clean up the code and allow easy changing       #
    # ------------------------------------------------------------------------ #
    register_path = "/register/"
    login_path = "/login/"

    test_user: dict[str, Union[str, bool]] = {
        "phone": "+998901234567",
        "email": "testuser@usertest.com",
        "full_name": "Test",
        "password": pwd_context.hash("test12345!"),
        "verified": True,
    }

    test_unverified_user = {
        **test_user,
        "verified": True,
    }

    test_banned_user = {
        **test_user,
        "banned": True,
    }

    # ------------------------------------------------------------------------ #
    #                          test '/register' route                          #
    # ------------------------------------------------------------------------ #
    @pytest.mark.asyncio()
    async def test_register_new_user(
        self, client: AsyncClient, test_db: AsyncSession, mocker
    ) -> None:
        """Ensure a new user can register."""


        post_body = {
            "phone": "+998921234567",
            "email": "testuser@testuser.com",
            "full_name": "Test",
            "password": "test12345!",
        }
        response = await client.post(
            self.register_path,
            json=post_body,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert list(response.json().keys()) == ["token", "refresh"]

        assert isinstance(response.json()["token"], str)
        assert isinstance(response.json()["refresh"], str)

        user_from_db = await test_db.get(User, 1)

        if user_from_db is None:
            pytest.fail("User was not added to the database")


        assert user_from_db.phone == post_body["phone"]
        assert user_from_db.email == post_body["email"]
        assert user_from_db.full_name == post_body["full_name"]
        assert user_from_db.password != post_body["password"]
        assert user_from_db.verified is True
        assert user_from_db.role == RoleType.user


    @pytest.mark.asyncio()
    async def test_register_duplicate_user(
        self, client: AsyncClient, test_db: AsyncSession, mocker
    ) -> None:
        post_body = {
            "phone": "+998921234567",
            "email": "testuser@testuser.com",
            "full_name": "Test",
            "password": "test12345!",
        }

        await client.post(
            self.register_path,
            json=post_body,
        )

        duplicate_user = await client.post(
            self.register_path,
            json=post_body,
        )

        assert duplicate_user.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio()
    async def test_password_is_stored_hashed(
        self, client, test_db, mocker
    ) -> None:
        """Ensure that the raw password is not stored in the database."""

        post_body = {
            "phone": "+998921234567",
            "email": "testuser@testuser.com",
            "full_name": "Test",
            "password": "test12345!",
        }
        await client.post(
            self.register_path,
            json=post_body,
        )

        user_from_db = await test_db.get(User, 1)

        assert user_from_db.password != post_body["password"]
        assert pwd_context.verify(post_body["password"], user_from_db.password)

    @pytest.mark.asyncio()
    async def test_register_new_user_with_bad_email(
        self, client, test_db, mocker
    ) -> None:
        """Ensure an invalid email address fails, and no email is sent."""

        response = await client.post(
            self.register_path,
            json={
                "phone": "+998921234567",
                "email": "testuser@testuser.com",
                "full_name": "Test",
                "password": "test12345!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "This email address is not valid"

        user_from_db = await test_db.get(User, 1)
        assert user_from_db is None


    @pytest.mark.parametrize(
        "post_body",
        [
            {},
            {
                "phone": "+998921234567",
                "email": "testuser@testuser.com",
                "full_name": "Test",
                "password": "test12345!",
            },
            {
                "phone": "+998921234567",
                "email": "testuser@testuser.com",
                "full_name": "",
                "password": "test12345!",
            },
            {
                "phone": "+998921234567",
                "email": "testuser@testuser.com",
                "full_name": "Test",
                "password": "",
            },
            {
                "phone": "+998921234567",
                "email": "testuser@testuser.com",
                "full_name": "Test",
                "password": "test12345!",
            },
        ],
    )
    @pytest.mark.asyncio()
    async def test_register_new_user_with_missing_data(
        self, client, test_db, mocker, post_body
    ) -> None:
        """Ensure registering with missing data fails, and no email is sent."""

        response = await client.post(self.register_path, json=post_body)

        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

        user_from_db = await test_db.get(User, 1)
        assert user_from_db is None


    # ------------------------------------------------------------------------ #
    #                            test '/login' route                           #
    # ------------------------------------------------------------------------ #
    @pytest.mark.asyncio()
    async def test_verified_user_can_login(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Ensure a validated user can log in."""
        test_db.add(User(**self.test_user))
        await test_db.commit()

        data = {
            "email": self.test_user["email"],
            "password": "test12345!",
        }

        response = await client.post(
            self.login_path,
            json=data,
        )

        assert response.status_code == status.HTTP_200_OK

        assert len(response.json()) == 2  # noqa: PLR2004
        assert list(response.json().keys()) == ["token", "refresh"]

        token, refresh = response.json().values()
        assert isinstance(token, str)
        assert isinstance(refresh, str)

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "post_body",
        [
            {
                "phone": "+998932004877",
                "password": "test12345!",
            },
            {
                "phone": "+998932004877",
                "password": "thisiswrong!",
            },
        ],
    )
    async def test_cant_login_with_wrong_email_or_password(
        self, client, test_db, post_body
    ) -> None:
        """Ensure the user cant login with wrong email or password."""
        test_db.add(User(**self.test_user))
        await test_db.commit()

        response = await client.post(
            self.login_path,
            json=post_body,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == UserErrorMessages.AUTH_INVALID

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "post_body",
        [
            {},
            {
                "password": "test12345!",
            },
            {
                "phone": "+998932004877",
            },
        ],
    )
    async def test_cant_login_with_missing_email_or_password(
        self, client, test_db, post_body
    ) -> None:
        """Ensure the user cant login with missing email or password."""
        test_db.add(User(**self.test_user))
        await test_db.commit()

        response = await client.post(
            self.login_path,
            json=post_body,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Field required" in response.json()["detail"][0]["msg"]



    @pytest.mark.asyncio()
    async def test_cant_login_with_banned_user(self, client, test_db) -> None:
        """Ensure the user cant login with banned user."""
        test_db.add(User(**self.test_banned_user))
        await test_db.commit()

        response = await client.post(
            self.login_path,
            json={
                "phone": self.test_banned_user["phone"],
                "password": "test12345!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == UserErrorMessages.AUTH_INVALID

    # ------------------------------------------------------------------------ #
    #                           test '/refresh' route                          #
    # ------------------------------------------------------------------------ #

    @pytest.mark.asyncio()
    async def test_refresh_token(self, client, test_db) -> None:
        """Ensure the user can refresh the token."""
        test_db.add(User(**self.test_user))
        await test_db.commit()

        login_response = await client.post(
            self.login_path,
            json={
                "phone": self.test_user["phone"],
                "password": "test12345!",
            },
        )

        refresh_response = await client.post(
            "/refresh/",
            json={
                "refresh": login_response.json()["refresh"],
            },
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert list(refresh_response.json().keys()) == ["token"]
        assert isinstance(refresh_response.json()["token"], str)

    @pytest.mark.asyncio()
    async def test_cant_refresh_token_with_invalid_refresh_token(
        self, client, test_db
    ) -> None:
        """Ensure the user cant refresh the token with invalid refresh token."""
        test_db.add(User(**self.test_user))
        await test_db.commit()

        refresh_response = await client.post(
            "/refresh/",
            json={
                "refresh": "invalid_refresh_token",
            },
        )

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert refresh_response.json()["detail"] == "That token is Invalid"

