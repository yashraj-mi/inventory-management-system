import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import engine, Base, AsyncSessionLocal
from scripts.seed_rbac import seed
from app.db.models.user import User
from app.db.models.rbac import Role, UserRole
from app.core.security import PasswordManager
from app.constants.common_enum import Status


async def reset_and_seed():
    print("Dropping all tables (CASCADE)...")
    async with engine.begin() as conn:
        from sqlalchemy import text

        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        # Also drop alembic version table if it exists in public
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))

    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Seeding RBAC roles...")
    await seed()

    print("Creating SUPER_ADMIN user...")
    async with AsyncSessionLocal() as db:
        role = await db.execute(select(Role).where(Role.name == "super_admin"))
        role = role.scalar_one_or_none()

        if not role:
            print("Error: super_admin role not found.")
            return

        user = User(
            first_name="Super",
            last_name="Admin",
            email="admin@gmail.com",
            password_hash=PasswordManager.hash_password("admin123"),
            status=Status.ACTIVE,
            user_roles=[UserRole(role_id=role.id)],
        )
        db.add(user)
        await db.commit()
        print("Super Admin created successfully!")
        print("Email: admin@gmail.com")
        print("Password: admin123")


if __name__ == "__main__":
    asyncio.run(reset_and_seed())
