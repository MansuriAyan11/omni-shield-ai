import hashlib
import json
from typing import Optional
from loguru import logger

from app.core.redis import redis_client, redis_available

class ImageHashCache:
    def __init__(self):
        # Using the centralized shared Redis configuration
        pass

    def calculate_sha256(self, file_path: str) -> str:
        """Compute SHA256 file checksum to identify duplicate files."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get(self, file_path: str) -> Optional[dict]:
        """Fetch moderation results from cache using the computed file hash."""
        try:
            file_hash = self.calculate_sha256(file_path)
            cache_key = f"image_cache:{file_hash}"
            
            if redis_available and redis_client:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit (Redis) for file hash: {file_hash}")
                    return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Error querying image cache: {e}")
            return None

    def set(self, file_path: str, result: dict, ttl: int = 604800) -> None:
        """Cache the moderation results for a file (default TTL: 7 days)."""
        try:
            # Do not cache error outputs
            if result.get("status") == "error":
                return
                
            file_hash = self.calculate_sha256(file_path)
            cache_key = f"image_cache:{file_hash}"
            
            # Add a 'cached' flag to distinguish real-time inference from cached retrieval
            cached_result = result.copy()
            cached_result["cached"] = True
            
            if redis_available and redis_client:
                redis_client.setex(cache_key, ttl, json.dumps(cached_result))
                logger.info(f"Successfully cached results in Redis for: {file_hash}")
        except Exception as e:
            logger.error(f"Error setting image cache: {e}")

# Singleton cache accessor
image_cache = ImageHashCache()
