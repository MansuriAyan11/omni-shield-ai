from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger

from app.models.user import User
from app.core.security import get_password_hash

class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Fetch a user by UUID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Fetch a user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, email: str, password: str, role: str = "client") -> User:
        """Create a new user in the database."""
        if len(password.encode("utf-8")) > 72:
            logger.warning(
                f"Password for {email} exceeds bcrypt's 72-byte limit and will be truncated"
            )

        hashed_password = get_password_hash(password)
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
