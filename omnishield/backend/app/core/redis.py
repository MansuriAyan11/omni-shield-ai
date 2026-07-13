import redis
from loguru import logger
from app.core.config import settings

redis_client = None
redis_available = False

try:
    # Set a low connection timeout to prevent blocking on network timeouts
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        socket_connect_timeout=1.5,
        decode_responses=True
    )
    redis_client.ping()
    redis_available = True
    logger.info("Shared Redis connection pool initialized successfully.")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Graceful degradation activated.")
    redis_available = False
