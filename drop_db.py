import asyncio
from app.core.database import engine, Base


async def drop_all_tables():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(drop_all_tables())
