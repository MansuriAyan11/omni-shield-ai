from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status, Header, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import verify_rate_limit
from app.models.user import User
from app.models.key import APIKey
from app.repositories.key_repo import APIKeyRepository

# JWT security bearer definition
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def _password_bytes(password: str) -> bytes:
    """Encode a plain-text password as UTF-8 bytes, truncated to bcrypt's 72-byte limit."""
    return password.encode("utf-8")[:72]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the plain password matches the stored bcrypt hash."""
    return bcrypt.checkpw(
        _password_bytes(plain_password),
        hashed_password.encode("utf-8"),
    )

def get_password_hash(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(
        _password_bytes(password),
        bcrypt.gensalt(),
    ).decode("utf-8")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT access token for a subject (user id)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(
    db: AsyncSession = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """Dependency to extract and validate JWT token, returning the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT Token decode failed: {e}")
        raise credentials_exception

    # Query DB for user - convert string UUID to UUID object
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user account"
        )
        
    return user

def require_role(allowed_roles: list[str]):
    """Role-Based Access Control decorator wrapper."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this resource"
            )
        return current_user
    return dependency

# Helper to update API Key use time out-of-band
async def update_key_last_used(db: AsyncSession, key_id: str) -> None:
    try:
        await db.execute(
            update(APIKey)
            .where(APIKey.id == key_id)
            .values(last_used=datetime.now(timezone.utc))
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to update API Key last_used timestamp: {e}")


async def get_api_key_user(
    background_tasks: BackgroundTasks,
    db: AsyncSession,
    x_api_key: str
) -> User:
    """Validate API Key, count rate limits, and return owner User."""
    hashed_key = APIKeyRepository.hash_key(x_api_key)
    api_key = await APIKeyRepository.get_active_by_hashed_key(db, hashed_key)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API Key."
        )
        
    # Enforce key-specific rate limits (RPM)
    await verify_rate_limit(f"apikey:{api_key.id}", api_key.rate_limit)
    
    # Asynchronously update usage timestamp
    background_tasks.add_task(update_key_last_used, db, api_key.id)
    
    # Retrieve owner user details
    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner account is suspended or inactive."
        )
        
    return user


async def get_current_client(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Resolve client identity from request. Checks for X-API-Key header first, 
    falling back to Authorization Bearer JWT.
    """
    x_api_key = request.headers.get("X-API-Key")
    auth_header = request.headers.get("Authorization")
    
    if x_api_key:
        return await get_api_key_user(background_tasks, db, x_api_key)
        
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        return await get_current_user(db, token)
        
    # Fallback to default rate limiting for public unauthenticated endpoints (can be set to reject)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials missing. Pass X-API-Key header or Authorization Bearer JWT token."
    )
