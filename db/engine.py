from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, relationship
from .models import Base, User, YandexDiskFolder

engine: AsyncEngine = create_async_engine(url="sqlite+aiosqlite:///instance/sqlite.db", echo=True)
async_session_maker: AsyncSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def async_create_table():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
