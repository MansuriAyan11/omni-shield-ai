"""
Create database tables without alembic
"""
import asyncio
from app.core.database import Base, async_engine
# Import all models to register them with Base
from app.models.user import User
from app.models.key import APIKey
from app.models.log import ModerationLog
from app.models.video_log import VideoModerationLog, VideoFrameFlag

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
