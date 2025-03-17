"""Define the User manager."""

from typing import Any, Optional, Type
from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from app.database.helpers import UserDB
from app.managers.auth import AuthManager
from app.models.users import User
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import RoleType
from app.schemas.user import UserChangePasswordRequest, UserEditRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ErrorMessages:
    """Define text error responses."""

    EMAIL_EXISTS = "A User with this email already exists"
    EMAIL_INVALID = "This email address is not valid"
    AUTH_INVALID = "Wrong phone or password"
    USER_INVALID = "This User does not exist"
    CANT_SELF_BAN = "You cannot ban/unban yourself!"
    NOT_VERIFIED = "You need to verify your Email before logging in"
    EMPTY_FIELDS = "You must supply all fields and they cannot be empty"
    ALREADY_BANNED_OR_UNBANNED = "This User is already banned/unbanned"


class UserManager:
    """Class to Manage the User."""

    @staticmethod
    async def register(user_data: dict[str, Any], session: AsyncSession) -> tuple[str, str]:

        """Register a new user."""
        # make sure relevant fields are not empty
        if not all(user_data.values()):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, ErrorMessages.EMPTY_FIELDS)

        # create a new dictionary to return, otherwise the original is modified
        # and can cause random testing issues
        new_user = user_data.copy()

        new_user["password"] = pwd_context.hash(user_data["password"])
        new_user["banned"] = False
        new_user["verified"] = True

        try:
            email_validation = validate_email(new_user["email"], check_deliverability=False)
            new_user["email"] = email_validation.email

            # actually add the new user to the database
            _ = await UserDB.create(session, user_data=new_user)
            await session.flush()

        except IntegrityError as err:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, ErrorMessages.EMAIL_EXISTS) from err

        except EmailNotValidError as err:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, ErrorMessages.EMAIL_INVALID) from err

        user_do = await UserDB.get(session, email=new_user["email"])
        assert user_do

        token = AuthManager.encode_token(user_do)
        refresh = AuthManager.encode_refresh_token(user_do)

        return token, refresh

    @staticmethod
    async def login(user_data: dict[str, str], session: AsyncSession) -> tuple[str, str]:
        """Log in an existing User using phone and password."""

        if "phone" not in user_data or "password" not in user_data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Phone and password are required")

        user_do = await UserDB.get(session, phone=user_data["phone"])

        if not user_do or not pwd_context.verify(user_data["password"], str(user_do.password)) or bool(user_do.banned):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid phone number or password")

        if not bool(user_do.verified):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your account is not verified")

        token = AuthManager.encode_token(user_do)
        refresh = AuthManager.encode_refresh_token(user_do)

        return token, refresh

    @staticmethod
    async def delete_user(user_id: int, session: AsyncSession) -> None:
        """Delete the User with specified ID."""
        check_user = await UserDB.get(session, user_id=user_id)
        if not check_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorMessages.USER_INVALID)

        await session.execute(delete(User).where(User.id == user_id))

    @staticmethod
    async def update_user(user_id: int, user_data: UserEditRequest, session: AsyncSession) -> None:
        """Update the User with specified ID."""
        check_user = await UserDB.get(session, user_id=user_id)
        if not check_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorMessages.USER_INVALID)

        await session.execute(
            update(User).where(User.id == user_id).values(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                password=pwd_context.hash(user_data.password),
            )
        )

    @staticmethod
    async def change_password(user_id: int, user_data: UserChangePasswordRequest, session: AsyncSession) -> None:
        """Change the specified user's Password."""
        check_user = await UserDB.get(session, user_id=user_id)
        if not check_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorMessages.USER_INVALID)

        await session.execute(
            update(User).where(User.id == user_id).values(password=pwd_context.hash(user_data.password))
        )

    @staticmethod
    async def set_ban_status(user_id: int, state: Optional[bool], my_id: int, session: AsyncSession) -> None:
        """Ban or un-ban the specified user based on supplied status."""
        if my_id == user_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, ErrorMessages.CANT_SELF_BAN)

        check_user = await UserDB.get(session, user_id)
        if not check_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorMessages.USER_INVALID)

        if bool(check_user.banned) == state:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, ErrorMessages.ALREADY_BANNED_OR_UNBANNED)

        await session.execute(update(User).where(User.id == user_id).values(banned=state))

    @staticmethod
    async def change_role(role: RoleType, user_id: int, session: AsyncSession) -> None:
        """Change the specified user's Role."""
        await session.execute(update(User).where(User.id == user_id).values(role=role))

    @staticmethod
    async def get_all_users(session: AsyncSession) -> Sequence[User]:
        """Get all Users."""
        return await UserDB.all(session)

    @staticmethod
    async def get_user_by_id(user_id: int, session: AsyncSession) -> Type[User]:
        """Return one user by ID."""
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorMessages.USER_INVALID)

        return user

    @staticmethod
    async def get_user_by_email(email: str, session: AsyncSession) -> User:
        """Return one user by Email."""
        user = await UserDB.get(session, email=email)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorMessages.USER_INVALID)

        return user
