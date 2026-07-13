import os
from typing import Set, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "OmniShield AI Moderation Platform"
    VERSION: str = "4.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development")  # development, staging, production

    # Security
    JWT_SECRET: str = Field(default="super_secret_jwt_sign_key_change_me_in_production_1298471203")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # OAuth2 Configuration (for future use)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./moderation.db")
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # Use the DATABASE_URL as-is for SQLite
        if self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL
        # Convert postgresql:// to postgresql+asyncpg:// if needed
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Cache & Task Queue
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    
    # Cache TTL settings
    IMAGE_CACHE_TTL: int = 604800  # 7 days in seconds
    API_RESPONSE_CACHE_TTL: int = 300  # 5 minutes

    # File Ingestion Parameters
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_CONTENT_TYPES: Set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }
    MAX_FILE_SIZE_MB: int = 10  # 10MB limit
    MAX_BATCH_SIZE: int = 100  # Maximum images in batch request

    # Video moderation
    VIDEO_UPLOAD_DIR: str = "uploads_video"
    ALLOWED_VIDEO_EXTENSIONS: Set[str] = {".mp4", ".avi", ".mov", ".webm", ".mkv"}
    MAX_VIDEO_SIZE_MB: int = 100
    VIDEO_FRAME_INTERVAL_SECONDS: float = 1.0

    # AI Moderation Thresholds
    DEFAULT_THRESHOLD: float = 0.50
    
    # Multi-Model AI Configuration
    ENABLE_NSFW_DETECTION: bool = True
    ENABLE_VIOLENCE_DETECTION: bool = True
    ENABLE_WEAPON_DETECTION: bool = True
    ENABLE_FACE_DETECTION: bool = True
    ENABLE_TEXT_MODERATION: bool = True
    
    # GPU Support
    USE_GPU: bool = Field(default=False)  # Set to True if GPU available
    GPU_DEVICE_ID: int = 0
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT_PER_MINUTE: int = 60
    ADMIN_RATE_LIMIT_PER_MINUTE: int = 300
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(default="*")  # In production, restrict to specific domains
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        # If it's a comma-separated string, split it
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return ["*"]
    
    # Cloud Storage - Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    
    # S3/AWS Configuration (optional)
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = "moderation-images"
    AWS_REGION: Optional[str] = "us-east-1"
    
    # Monitoring
    ENABLE_PROMETHEUS_METRICS: bool = True
    SENTRY_DSN: Optional[str] = None  # For error tracking
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret_in_production(cls, v: str, info) -> str:
        # Access other fields via info.data
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and "change_me" in v.lower():
            raise ValueError(
                "JWT_SECRET must be changed in production! "
                "Generate a secure secret with: openssl rand -hex 32"
            )
        return v

settings = Settings()

# Log configuration warnings
if settings.ENVIRONMENT == "production":
    if settings.CORS_ORIGINS == "*":
        import warnings
        warnings.warn(
            "CORS is allowing all origins in production! "
            "Set CORS_ORIGINS to specific domains.",
            UserWarning
        )
