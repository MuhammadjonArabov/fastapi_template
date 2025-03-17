from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, validator
import re

from app.models.enums import RoleType


class UserBase(BaseModel):
    """Base for the User Schema."""
    phone: str
    password: str

    @validator("phone")
    def validate_phone(cls, value: str) -> str:
        """Check if phone number matches the Uzbekistan format +998xxxxxxxxx."""
        pattern = r"^\+998\d{9}$"
        if not re.match(pattern, value):
            raise ValueError("Invalid phone number format! Use: +998xx xxx xx xx")
        return value

    model_config = ConfigDict(from_attributes=True)


class UserRegisterRequest(UserBase):
    """Request schema for the Register Route."""
    email: str
    full_name: str


class UserLoginRequest(BaseModel):
    """Request schema for the Login Route."""
    phone: str
    password: str

class TokenRefreshRequest(BaseModel):
    """Request schema for refreshing a JWT token."""
    refresh: str

class UserChangePasswordRequest(BaseModel):
    """Request Schema for changing a user's password."""
    password: str

class UserEditRequest(UserBase):
    """Request schema for Editing a User."""
    email: str
    full_name: str

class TokenResponse(BaseModel):
    """Response Schema for Register/Login routes."""
    token: str
    refresh: str

class TokenRefreshResponse(BaseModel):
    """Return a new JWT only, after a refresh request."""
    token: str

class GetUsers(BaseModel):
    id: int
    full_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    role: RoleType
    banned: bool