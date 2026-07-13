import secrets
import hashlib
from typing import List, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.key import APIKey

class APIKeyRepository:
    @staticmethod
    def generate_raw_key() -> str:
        """Generate a cryptographically secure random API key prefixed with ak_."""
        token = secrets.token_urlsafe(32)
        return f"ak_{token}"

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Hash the raw key using SHA256 for secure storage."""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    async def get_by_id(db: AsyncSession, key_id: str) -> Optional[APIKey]:
        """Fetch API key model by ID."""
        from uuid import UUID
        key_uuid = UUID(key_id) if isinstance(key_id, str) else key_id
        result = await db.execute(select(APIKey).where(APIKey.id == key_uuid))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str) -> List[APIKey]:
        """Fetch all API keys belonging to a user."""
        from uuid import UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        result = await db.execute(select(APIKey).where(APIKey.user_id == user_uuid))
        return result.scalars().all()

    @staticmethod
    async def get_active_by_hashed_key(db: AsyncSession, hashed_key: str) -> Optional[APIKey]:
        """Fetch active API key model by its SHA256 hash."""
        result = await db.execute(
            select(APIKey).where(
                APIKey.hashed_key == hashed_key,
                APIKey.status == "active"
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_id: str, name: str, rate_limit: int = 60) -> tuple[APIKey, str]:
        """Create a new API key in the DB. Returns the DB model and the raw (unhashed) key."""
        from uuid import UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        raw_key = APIKeyRepository.generate_raw_key()
        hashed_key = APIKeyRepository.hash_key(raw_key)
        
        db_key = APIKey(
            user_id=user_uuid,
            hashed_key=hashed_key,
            name=name,
            rate_limit=rate_limit
        )
        
        db.add(db_key)
        await db.commit()
        await db.refresh(db_key)
        return db_key, raw_key

    @staticmethod
    async def revoke(db: AsyncSession, key_id: str) -> Optional[APIKey]:
        """Revoke an API key by marking its status as revoked."""
        db_key = await APIKeyRepository.get_by_id(db, key_id)
        if db_key:
            db_key.status = "revoked"
            await db.commit()
            await db.refresh(db_key)
        return db_key
