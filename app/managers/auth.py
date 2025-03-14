"""Define the Autorization Manager."""

import datetime
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.settings import get_settings
from app.database.db import get_database
from app.database.helpers import UserDB
from app.models.enums import RoleType
from app.schemas.user import TokenRefreshRequest


class ResponseMessages:
    """Error strings for different circumstances."""

    CANT_GENERATE_JWT = "Unable to generate the JWT"
    CANT_GENERATE_REFRESH = "Unable to generate the Refresh Token"
    CANT_GENERATE_VERIFY = "Unable to generate the Verification Token"
    INVALID_TOKEN = "That token is Invalid"  # noqa: S105
    EXPIRED_TOKEN = "That token has Expired"  # noqa: S105
    VERIFICATION_SUCCESS = "User succesfully Verified"
    USER_NOT_FOUND = "User not Found"
    ALREADY_VALIDATED = "You are already validated"
    VALIDATION_RESENT = "Validation email re-sent"


class AuthManager:
    """Handle the JWT Auth."""

    @staticmethod
    def encode_token(user: User) -> str:
        """Create and return a JTW token."""
        try:
            payload = {
                "sub": user.id,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                       + datetime.timedelta(minutes=get_settings().access_token_expire_minutes),
            }
            return jwt.encode(payload, get_settings().secret_key, algorithm="HS256")

        except (jwt.PyJWTError, AttributeError) as exc:
            # log the exception
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.CANT_GENERATE_JWT) from exc

    @staticmethod
    def encode_refresh_token(user: User) -> str:
        """Create and return a JTW token."""
        try:
            payload = {
                "sub": user.id,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=60 * 24 * 30),
                "typ": "refresh",
            }
            return jwt.encode(payload, get_settings().secret_key, algorithm="HS256")

        except (jwt.PyJWTError, AttributeError) as exc:
            # log the exception
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.CANT_GENERATE_REFRESH) from exc

    @staticmethod
    def encode_verify_token(user: User) -> str:
        """Create and return a JTW token."""
        try:
            payload = {
                "sub": user.id,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=10),
                "typ": "verify",
            }
            return jwt.encode(payload, get_settings().secret_key, algorithm="HS256")

        except (jwt.PyJWTError, AttributeError) as exc:
            # log the exception
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.CANT_GENERATE_VERIFY) from exc

    @staticmethod
    async def refresh(refresh_token: TokenRefreshRequest, session: AsyncSession) -> str:
        """Refresh an expired JWT token, given a valid Refresh token."""
        try:
            payload = jwt.decode(refresh_token.refresh, get_settings().secret_key, algorithms=["HS256"])

            if payload["typ"] != "refresh":
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.INVALID_TOKEN)

            user_data = await UserDB.get(session, user_id=payload["sub"])

            if not user_data:
                raise HTTPException(status.HTTP_404_NOT_FOUND, ResponseMessages.USER_NOT_FOUND)

            # block a banned user
            if bool(user_data.banned):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.INVALID_TOKEN)

            new_token = AuthManager.encode_token(user_data)

        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.EXPIRED_TOKEN) from exc

        except jwt.InvalidTokenError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.INVALID_TOKEN) from exc
        else:
            return new_token


class CustomHTTPBearer(HTTPBearer):
    """Our own custom HTTPBearer class."""

    async def __call__(self, request: Request, db: AsyncSession = Depends(get_database)) -> Optional[
        HTTPAuthorizationCredentials]:
        """Override the default __call__ function."""
        res = await super().__call__(request)

        try:
            if res:
                payload = jwt.decode(res.credentials, get_settings().secret_key, algorithms=["HS256"])
                user_data = await UserDB.get(db, user_id=payload["sub"])
                # block a banned or unverified user
                if user_data:
                    if bool(user_data.banned):
                        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.INVALID_TOKEN)
                    request.state.user = user_data

        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.EXPIRED_TOKEN) from exc

        except jwt.InvalidTokenError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ResponseMessages.INVALID_TOKEN) from exc

        else:
            return user_data


oauth2_schema = CustomHTTPBearer()


def is_admin(request: Request) -> None:
    """Block if user is not an Admin."""
    if request.state.user.role != RoleType.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")


def can_edit_user(request: Request) -> None:
    """Check if the user can edit this resource. True if they own the resource or are Admin"""

    if request.state.user.role != RoleType.admin and request.state.user.id != int(request.path_params["user_id"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")


def is_banned(request: Request) -> None:
    """Don't let banned users access the route."""

    if request.state.user.banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Banned!")
