"""
Advanced Rate Limiting with SlowAPI
Provides IP-based rate limiting alongside existing user/key-based limits
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings

# Initialize SlowAPI limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.DEFAULT_RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors
    
    Returns structured JSON response with retry information
    """
    logger.warning(
        f"Rate limit exceeded for IP {get_remote_address(request)}. "
        f"Limit: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "detail": exc.detail,
            "retry_after": 60  # seconds
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(settings.DEFAULT_RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(__import__('time').time()) + 60)
        }
    )


# Rate limit decorators for different tiers
def public_rate_limit():
    """Rate limit for public/unauthenticated endpoints"""
    return limiter.limit(f"{settings.DEFAULT_RATE_LIMIT_PER_MINUTE}/minute")


def authenticated_rate_limit():
    """Rate limit for authenticated users"""
    return limiter.limit(f"{settings.DEFAULT_RATE_LIMIT_PER_MINUTE * 2}/minute")


def admin_rate_limit():
    """Rate limit for admin users"""
    return limiter.limit(f"{settings.ADMIN_RATE_LIMIT_PER_MINUTE}/minute")


def no_rate_limit():
    """Exempt from rate limiting (use sparingly)"""
    return limiter.exempt


# Custom key functions for more granular control
def get_user_or_ip(request: Request) -> str:
    """
    Get rate limit key: user ID if authenticated, otherwise IP address
    """
    # Try to get user from token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from app.core.security import jwt
            from app.core.config import settings as app_settings
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(
                token, 
                app_settings.JWT_SECRET, 
                algorithms=[app_settings.JWT_ALGORITHM]
            )
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    
    # Try to get API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:16]}"  # Use prefix to avoid leaking keys
    
    # Fallback to IP
    return f"ip:{get_remote_address(request)}"


def get_endpoint_key(request: Request) -> str:
    """
    Rate limit per endpoint per user/IP
    """
    base_key = get_user_or_ip(request)
    endpoint = request.url.path
    return f"{base_key}:{endpoint}"
