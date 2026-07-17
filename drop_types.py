import asyncio
from sqlalchemy import text
from app.core.database import engine


async def drop_enum_types():
    print("Dropping residual ENUM types from PostgreSQL...")
    types_to_drop = ["sales_order_status"]

    async with engine.begin() as conn:
        for enum_type in types_to_drop:
            # We use IF EXISTS and CASCADE to ensure clean removal
            query = text(f"DROP TYPE IF EXISTS {enum_type} CASCADE;")
            await conn.execute(query)
            print(f"Dropped type: {enum_type}")

    print("All residual ENUM types dropped successfully!")


if __name__ == "__main__":
    asyncio.run(drop_enum_types())
