import asyncio
from app.database.db import async_session
from app.database.helpers import get_user_by_phone_
from app.models.users import User
from app.models.enums import RoleType
from app.database.helpers import hash_password


async def create_admin():
    """Create an admin user."""
    phone = input("Phone: ")
    password = input("Password: ")

    async with async_session() as db:
        existing_user = await get_user_by_phone_(phone, db)

        if existing_user:
            print("This phone number already exists!")
            return

        admin_user = User(
            phone=phone,
            password=hash_password(password),
            role=RoleType.admin,
            verified=True,
            banned=False
        )

        db.add(admin_user)
        await db.commit()
        print("OK 😎. Create admin 🎊🎉")


if __name__ == "__main__":
    asyncio.run(create_admin())
