import pytest
import os
import sys
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add backend root to path so tests can find app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import Base, get_db

# Use an isolated SQLite file for local unit tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_api.db"

engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Sync wrapper to create and tear down the test SQLite database without triggering asyncio scope conflicts."""
    loop = asyncio.new_event_loop()
    
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    # Initialize tables
    loop.run_until_complete(create_tables())
    yield
    # Tear down tables
    loop.run_until_complete(drop_tables())
    loop.close()
    
    # Clean up test DB file
    if os.path.exists("./test_api.db"):
        try:
            os.remove("./test_api.db")
        except Exception:
            pass

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session for a single test transaction, rolling back modifications."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Provide a TestClient with the database dependency overridden asynchronously."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
