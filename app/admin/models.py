"""Define the admin views for the models."""

from typing import Any, ClassVar, Union
from fastapi import Request
from sqladmin import ModelView
from sqlalchemy.orm import InstrumentedAttribute

from app.database.helpers import hash_password
from app.models.users import User


class UserAdmin(ModelView, model=User):
    """Admin view for the User model."""

    column_list: ClassVar[list[Any]] = [
        User.id,
        User.phone,
        User.verified,
        User.role,
        User.banned,
    ]

    column_labels: ClassVar[dict[Union[str, InstrumentedAttribute[Any]], str]] = {
        "id": "User ID",
        "phone": "Phone",
        "verified": "Verified",
        "role": "Role",
        "banned": "Banned",
        "full_name": "Full Name",
    }

    column_details_exclude_list: ClassVar[list[Any]] = [User.password]

    form_create_rules: ClassVar[list[str]] = [
        "phone",
        "password",
        "full_name",
        "verified",
        "role",
        "banned",
    ]
    form_edit_rules: ClassVar[list[str]] = [
        "phone",
        "full_name",
        "verified",
        "role",
        "banned",
    ]

    icon = "fa-solid fa-user"

    async def on_model_change(
            self,
            data: dict[str, Any],
            _model: User,
            is_created: bool,
            _request: Request,
    ) -> None:
        """Customize the password hash before saving into DB."""
        if is_created:
            data["password"] = hash_password(data["password"])
