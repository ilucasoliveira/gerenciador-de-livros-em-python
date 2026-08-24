import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE) 

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()