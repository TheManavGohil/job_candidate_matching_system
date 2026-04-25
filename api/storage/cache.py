"""
Redis cache helpers.
"""

import json
import logging
import pickle
from typing import Optional, Any

import redis

from api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Return a Redis connection (lazy singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
        )
        try:
            _redis_client.ping()
            logger.info("Connected to Redis")
        except redis.ConnectionError:
            logger.warning("Redis not available — caching disabled")
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """Retrieve a cached value (pickle-deserialized)."""
    try:
        r = get_redis()
        data = r.get(key)
        if data:
            return pickle.loads(data)
    except Exception as e:
        logger.debug(f"Cache miss for {key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl: int = 3600):
    """Store a value in cache with TTL (pickle-serialized)."""
    try:
        r = get_redis()
        r.setex(key, ttl, pickle.dumps(value))
    except Exception as e:
        logger.debug(f"Cache set failed for {key}: {e}")


def cache_delete(key: str):
    """Delete a cached key."""
    try:
        r = get_redis()
        r.delete(key)
    except Exception as e:
        logger.debug(f"Cache delete failed for {key}: {e}")


def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern."""
    try:
        r = get_redis()
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception as e:
        logger.debug(f"Cache delete pattern failed for {pattern}: {e}")


def invalidate_match_cache():
    """Invalidate all match results — called after candidate upload."""
    cache_delete_pattern("match:*")
    logger.info("Invalidated all match caches")
