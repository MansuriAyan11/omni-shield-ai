from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserCreate, UserResponse, Token, UserRegisterSchema
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register(user_data: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
    try:
        existing_user = await UserRepository.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            role="client",
            status="active",
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {"success": True, "message": "User registered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(status_code=400, detail=f"Registration failed core process: {str(e)}")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate credentials and return a JWT access token (Swagger compatible)."""
    try:
        # OAuth2 username corresponds to user email
        logger.info(f"Login attempt for user: {form_data.username}")
        user = await UserRepository.get_by_email(db, form_data.username)
        
        if not user:
            logger.warning(f"Login failed: User not found - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password"
            )
        
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Login failed: Invalid password for user - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password"
            )
        
        if user.status != "active":
            logger.warning(f"Login failed: Account deactivated - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # Generate JWT token
        access_token = create_access_token(subject=user.id)
        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Login process crashed due to: {str(e)}")
        logger.exception("Full traceback:")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database operational error: {str(e)}"
        )
