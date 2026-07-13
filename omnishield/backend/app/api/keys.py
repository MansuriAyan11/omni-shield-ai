from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.repositories.key_repo import APIKeyRepository
from app.schemas.key import APIKeyCreate, APIKeyResponse, APIKeyNewResponse

router = APIRouter(prefix="/keys", tags=["API Keys"])

@router.post("/", response_model=APIKeyNewResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new API key for the current user client (raw key returned only once)."""
    try:
        db_key, raw_key = await APIKeyRepository.create(
            db, 
            user_id=current_user.id, 
            name=key_data.name, 
            rate_limit=key_data.rate_limit
        )
        logger.info(f"Generated new API Key '{db_key.name}' for user {current_user.email}")
        return {
            "key_details": db_key,
            "raw_key": raw_key
        }
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API Key"
        )

@router.get("/", response_model=List[APIKeyResponse])
async def list_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all API keys belonging to the logged-in user client."""
    try:
        keys = await APIKeyRepository.get_by_user(db, current_user.id)
        return keys
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )

@router.delete("/{key_id}", response_model=APIKeyResponse)
async def revoke_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key, preventing any further authentication using it."""
    db_key = await APIKeyRepository.get_by_id(db, key_id)
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )
    
    # Enforce ownership check
    if db_key.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this key"
        )
        
    try:
        revoked_key = await APIKeyRepository.revoke(db, key_id)
        logger.info(f"Revoked API Key ID {key_id} for user {current_user.email}")
        return revoked_key
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API Key"
        )
