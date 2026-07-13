from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# 1. Sync engine (used for migrations/seeding/CLI)
sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# 2. Async engine (used for high-performance FastAPI routes)
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_pre_ping=True
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# 3. Declarative Base
Base = declarative_base()

# 4. FastAPI DB Session Dependency Providers
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async session generator for injection in endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db() -> Generator:
    """Sync session generator for synchronous tasks/scripts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
