from app.models.users import User
from typing import Any
from sqlalchemy import select
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from typing import Any, Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserDB:

    @staticmethod
    async def all(session: AsyncSession) -> Sequence[User]:
        """Return all Users in the database."""
        result = await session.execute(select(User))
        return result.scalars().all()

    @staticmethod
    async def get(session: AsyncSession, user_id: int | None = None, email: str | None = None) -> User | None:
        if user_id:
            """Return a specific user by their email address."""
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalars().first()

        elif email:
            """Return a specific user by their email address."""
            result = await session.execute(select(User).where(User.email == email))
            return result.scalars().first()

        else:
            raise ValueError("Provide user_id or email to get related user.")

    @staticmethod
    async def create(session: AsyncSession, user_data: dict[str, Any]) -> User:
        """Add a new user to the database."""
        new_user = User(**user_data)
        session.add(new_user)
        return new_user


def hash_password(password: str) -> str:
    """Hash a password.

    Args:
        password: The password to hash

    Returns:
        str: The hashed password

    Raises:
        ValueError: If password is empty
    """
    value_error = "Password cannot be empty"

    if not password:
        raise ValueError(value_error)
    return pwd_context.hash(password)


async def get_user_by_id_(
        user_id: int, session: AsyncSession
) -> Optional[User]:
    """Return a user by ID."""
    return await session.get(User, user_id)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password.

    Args:
        password: The password to verify
        hashed_password: The hashed password to verify against

    Returns:
        bool: True if password matches, False otherwise

    Raises:
        ValueError: If password or hash is empty
    """
    error_empty = "Password and hash cannot be empty"
    error_invalid = "Invalid hash format"

    if not password or not hashed_password:
        raise ValueError(error_empty)
    try:
        return pwd_context.verify(password, hashed_password)
    except Exception as exc:
        # Handle malformed hash errors from passlib
        raise ValueError(error_invalid) from exc


async def get_user_by_email_(
        email: str, session: AsyncSession
) -> Optional[User]:
    """Return a user by email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone_(phone: str, db: AsyncSession):
    '''Find a user by phone number'''
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalars().first()
