from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.db import get_database
from app.managers.auth import AuthManager
from app.managers.user import UserManager
from app.models.users import User
from app.schemas.user import UserLoginRequest, UserRegisterRequest, TokenRefreshRequest, TokenRefreshResponse, \
    TokenResponse, GetUsers

router = APIRouter(tags=["Authentication"])


@router.post("/register/", status_code=status.HTTP_201_CREATED, name="register_a_new_user", response_model=TokenResponse)
async def register(user_data: UserRegisterRequest, session: AsyncSession = Depends(get_database)) -> dict[str, str]:
    """Register a new User and return a JWT token plus a Refresh Token."""
    token, refresh = await UserManager.register(user_data.model_dump(), session=session)
    return {"token": token, "refresh": refresh}


@router.post("/login/", response_model=TokenResponse)
async def login(user_data: UserLoginRequest, session: AsyncSession = Depends(get_database)):
    """Login user with phone and password"""
    token, refresh = await UserManager.login(user_data.model_dump(), session)
    return {"token": token, "refresh": refresh}



@router.post("/refresh/", name="refresh_an_expired_token", response_model=TokenRefreshResponse)
async def generate_refresh_token(refresh_token: TokenRefreshRequest, session: AsyncSession = Depends(get_database)) -> dict[str, str]:
    """Return a new JWT, given a valid Refresh token."""
    token = await AuthManager.refresh(refresh_token, session)
    return {"token": token}

@router.get("/users/", name="get_users", response_model=List[GetUsers])
async def get_users(session: AsyncSession = Depends(get_database)) -> List[GetUsers]:
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users