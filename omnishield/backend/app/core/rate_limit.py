import time
from fastapi import HTTPException, status
from loguru import logger

from app.core.redis import redis_client, redis_available

async def verify_rate_limit(identifier: str, limit_per_minute: int) -> None:
    """
    Check if a client identifier has exceeded their rate limit.
    Uses Redis windowed counting and fails open (gracefully degradation) if Redis is down.
    """
    if not redis_available or not redis_client:
        # Fallback: if cache server is down, do not block the request
        return

    # Create a unique key for the current minute
    current_minute = int(time.time() // 60)
    rate_key = f"rate_limit:{identifier}:{current_minute}"

    try:
        # Run atomic increment and set TTL in a pipeline
        pipe = redis_client.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 59) # Expire at the end of the current minute
        results = pipe.execute()
        
        request_count = results[0]
        
        if request_count > limit_per_minute:
            logger.warning(f"Rate limit hit: client '{identifier}' made {request_count} requests (limit: {limit_per_minute} rpm)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "success": False,
                    "message": "Too many requests. Please slow down.",
                    "limit": limit_per_minute,
                    "retry_after": 60 - int(time.time() % 60)
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redis rate limiting pipeline failed: {e}")
