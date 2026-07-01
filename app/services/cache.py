import json
import logging
import time
import fnmatch
from typing import Any, Optional, Dict, Tuple
from app.core.config import settings

logger = logging.getLogger("app.services.cache")


class CacheService:
    """
    Production-ready Caching service backed by Redis.
    Provides automatic fallback to an in-memory database dictionary if Redis is unavailable.
    """
    def __init__(self, redis_url: Optional[str] = None) -> None:
        self.redis_client = None
        self._in_memory_db: Dict[str, Tuple[str, float]] = {}  # key -> (json_val, expire_time)
        
        url = redis_url or settings.REDIS_URL
        if url:
            try:
                import redis
                self.redis_client = redis.from_url(url, decode_responses=True)
                # Test the connection via ping
                self.redis_client.ping()
                logger.info(f"Connected to Redis cache successfully at: {url}")
            except Exception as exc:
                logger.warning(
                    f"Redis connection failed at {url}. Falling back to in-memory caching. Details: {exc}"
                )
                self.redis_client = None
        else:
            logger.info("No REDIS_URL configured. Using in-memory dictionary cache fallback.")

    def get(self, key: str) -> Optional[Any]:
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as exc:
                logger.error(f"CacheService Redis GET error for key '{key}': {exc}")
            return None
        else:
            item = self._in_memory_db.get(key)
            if not item:
                return None
            val_str, expire_at = item
            if expire_at and expire_at < time.time():
                self.delete(key)
                return None
            return json.loads(val_str)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            # Use default=str to convert non-standard objects like UUIDs or datetime to strings
            val_str = json.dumps(value, default=str)
        except Exception as exc:
            logger.error(f"CacheService serialization error for key '{key}': {exc}")
            return False
        if self.redis_client:
            try:
                if ttl:
                    self.redis_client.setex(key, ttl, val_str)
                else:
                    self.redis_client.set(key, val_str)
                return True
            except Exception as exc:
                logger.error(f"CacheService Redis SET error for key '{key}': {exc}")
                return False
        else:
            expire_at = (time.time() + ttl) if ttl else 0.0
            self._in_memory_db[key] = (val_str, expire_at)
            return True

    def delete(self, key: str) -> bool:
        if self.redis_client:
            try:
                return bool(self.redis_client.delete(key))
            except Exception as exc:
                logger.error(f"CacheService Redis DELETE error for key '{key}': {exc}")
                return False
        else:
            if key in self._in_memory_db:
                del self._in_memory_db[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        if self.redis_client:
            try:
                return bool(self.redis_client.exists(key))
            except Exception as exc:
                logger.error(f"CacheService Redis EXISTS error for key '{key}': {exc}")
                return False
        else:
            if key in self._in_memory_db:
                _, expire_at = self._in_memory_db[key]
                if expire_at and expire_at < time.time():
                    self.delete(key)
                    return False
                return True
            return False

    def ttl(self, key: str) -> int:
        if self.redis_client:
            try:
                return int(self.redis_client.ttl(key))
            except Exception as exc:
                logger.error(f"CacheService Redis TTL error for key '{key}': {exc}")
                return -1
        else:
            if key in self._in_memory_db:
                _, expire_at = self._in_memory_db[key]
                if not expire_at:
                    return -1
                remaining = int(expire_at - time.time())
                return max(remaining, -1)
            return -2

    def clear(self) -> bool:
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                return True
            except Exception as exc:
                logger.error(f"CacheService Redis FLUSHDB error: {exc}")
                return False
        else:
            self._in_memory_db.clear()
            return True

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidates all keys matching a glob pattern (e.g. 'registries:*').
        """
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            except Exception as exc:
                logger.error(f"CacheService Redis keys invalidation error for pattern '{pattern}': {exc}")
                return 0
        else:
            count = 0
            matched_keys = [k for k in self._in_memory_db.keys() if fnmatch.fnmatch(k, pattern)]
            for k in matched_keys:
                if self.delete(k):
                    count += 1
            return count


# Initialize single global cache service instance
cache_service = CacheService()
