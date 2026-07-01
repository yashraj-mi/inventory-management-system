import asyncio
import sys
import os
from app.core.config import get_settings

# Ensure the root directory is in the PYTHONPATH so we can import `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import AsyncSessionLocal
from app.db.models.organization import Organization
from app.constants.organization_enum import OrganizationStatus
from app.db.models.user import User
from app.constants.user_enum import UserRole
from app.core.security import PasswordManager

settings = get_settings()


async def init_db():
    """
    Seeds the database with a foundational System Organization and a Super Admin.
    """
    print("Starting database initialization...")

    # Table creation is now handled by Alembic migrations
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            # 1. Create the System Organization
            print("Creating System Organization...")
            system_org = Organization(
                name="System Administrators",
                email=settings.ADMIN_EMAIL,
                phone="0000000000",
                address="Internal System",
                status=OrganizationStatus.ACTIVE,
            )

            session.add(system_org)
            await session.flush()  # Flush to generate the system_org.id
            print(f"System Organization created with ID: {system_org.id}")

            # 2. Create the first Super Admin user
            print("Creating Super Admin User...")
            hashed_password = PasswordManager.hash_password(settings.ADMIN_PASSWORD)

            super_admin = User(
                organization_id=system_org.id,
                role=UserRole.SUPER_ADMIN,
                first_name="Super",
                last_name="Admin",
                email=settings.ADMIN_EMAIL,
                password_hash=hashed_password,
            )

            session.add(super_admin)
            await session.commit()

            print("------------------------------------------")
            print("Super Admin created successfully!")
            print("------------------------------------------")

        except Exception as e:
            print(f"An error occurred during initialization: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(init_db())
