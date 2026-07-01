import time
import pytest
from app.services.cache import CacheService


def test_in_memory_cache_operations():
    """
    Tests the CacheService using the in-memory fallback.
    """
    # Initialize cache service with no Redis URL to force in-memory dictionary fallback
    cache = CacheService(redis_url=None)
    
    assert cache.redis_client is None
    
    # 1. Set & Get
    assert cache.set("test_key", {"foo": "bar"}, ttl=10) is True
    assert cache.get("test_key") == {"foo": "bar"}
    
    # 2. Exists
    assert cache.exists("test_key") is True
    assert cache.exists("nonexistent_key") is False
    
    # 3. TTL
    assert cache.ttl("test_key") > 0
    assert cache.ttl("nonexistent_key") == -2
    
    # 4. Invalidation by glob pattern
    cache.set("registries:1", "data1")
    cache.set("registries:2", "data2")
    cache.set("projects:1", "data3")
    
    deleted_count = cache.invalidate_pattern("registries:*")
    assert deleted_count == 2
    assert cache.get("registries:1") is None
    assert cache.get("registries:2") is None
    assert cache.get("projects:1") == "data3"
    
    # 5. Clear
    cache.clear()
    assert cache.get("projects:1") is None
    assert len(cache._in_memory_db) == 0


def test_in_memory_cache_expiration():
    """
    Checks that keys expire correctly under the in-memory cache system.
    """
    cache = CacheService(redis_url=None)
    
    # Set key with 1 second TTL
    cache.set("expire_key", "val", ttl=1)
    assert cache.get("expire_key") == "val"
    
    # Wait for expiration
    time.sleep(1.1)
    
    assert cache.get("expire_key") is None
    assert cache.exists("expire_key") is False
