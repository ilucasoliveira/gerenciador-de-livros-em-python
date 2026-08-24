import asyncio
from app.models import Base
from app.database import engine

async def create_async_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_async_tables())