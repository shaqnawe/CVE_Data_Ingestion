import os
import redis
from dotenv import load_dotenv
import json
from typing import Type, TypeVar
from pydantic import BaseModel
import logging

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis(decode_responses=True).from_url(REDIS_URL)

T = TypeVar("T", bound=BaseModel)

CACHE_VERSION = "v1"  # Increment this to invalidate all old cache entries
logger = logging.getLogger("cache")


def set_cache(key: str, value, ttl: int = 300) -> None:
    """
    Store a value in Redis cache with optional TTL (in seconds).
    Serializes value as JSON.
    """
    versioned_key = f"{CACHE_VERSION}:{key}"
    serialized = json.dumps(value)
    try:
        redis_client.setex(versioned_key, ttl, serialized)
        logger.info(f"[CACHE SET] {versioned_key}")
    except Exception as e:
        logger.error(f"[CACHE ERROR][SET] {versioned_key}: {e}")


def get_cache(key: str):
    """
    Retrieve a value from Redis cache by key.
    Deserializes JSON to Python object. Returns None if not found.
    Logs cache hits and misses.
    Handles Redis connection errors gracefully.
    """
    versioned_key = f"{CACHE_VERSION}:{key}"
    try:
        cached = redis_client.get(versioned_key)
        if cached is None:
            logger.info(f"[CACHE MISS] {versioned_key}")
            return None
        if not isinstance(cached, str):
            logger.warning(
                f"[CACHE TYPE WARNING] {versioned_key} is not a string. Type: {type(cached)}"
            )
            return None
        logger.info(f"[CACHE HIT] {versioned_key}")
        try:
            return json.loads(cached)
        except Exception:
            logger.warning(f"[CACHE FALLBACK][NOT JSON] {versioned_key}")
            return cached  # fallback if not JSON
    except Exception as e:
        logger.error(f"[CACHE ERROR][GET] {versioned_key}: {e}")
        return None


def delete_cache(key: str) -> None:
    """
    Delete a specific cache entry by key.
    """
    versioned_key = f"{CACHE_VERSION}:{key}"
    try:
        redis_client.delete(versioned_key)
        logger.info(f"[CACHE DELETE] {versioned_key}")
    except Exception as e:
        logger.error(f"[CACHE ERROR][DELETE] {versioned_key}: {e}")


def invalidate_cache_pattern(pattern: str) -> None:
    """
    Delete all cache entries matching a given pattern (e.g., 'cves:*').
    Use with caution! This can be expensive on large datasets.
    """
    versioned_pattern = f"{CACHE_VERSION}:{pattern}"
    try:
        for key in redis_client.scan_iter(versioned_pattern):
            redis_client.delete(key)
            logger.info(f"[CACHE DELETE] {key}")
    except Exception as e:
        logger.error(f"[CACHE ERROR][PATTERN DELETE] {versioned_pattern}: {e}")


def make_cache_key(base: str, **kwargs) -> str:
    """
    Generate a consistent, collision-free cache key using a base and keyword arguments.
    Example: make_cache_key('cves', skip=0, limit=10) -> 'cves:limit=10:skip=0'
    Keys are sorted for consistency.
    """
    if not kwargs:
        return base
    parts = [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return f"{base}:" + ":".join(parts)


def serialize_model(model: BaseModel) -> str:
    """
    Serialize a Pydantic model to a JSON string.
    """
    return model.model_dump_json()


def deserialize_model(data, model_class: Type[T]) -> T:
    """
    Deserialize a JSON string or dict to a Pydantic model instance.
    """
    if isinstance(data, str):
        return model_class.model_validate_json(data)
    elif isinstance(data, dict):
        return model_class.model_validate(data)
    else:
        raise ValueError("Data must be a JSON string or dict.")
