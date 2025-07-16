import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis(decode_responses=True).from_url(REDIS_URL)


def set_cache(key: str, value, ttl: int = 300) -> None:
    """
    Store a value in Redis cache with optional TTL (in seconds).
    Serializes value as JSON.
    """
    serialized = json.dumps(value)
    redis_client.setex(key, ttl, serialized)


def get_cache(key: str):
    """
    Retrieve a value from Redis cache by key.
    Deserializes JSON to Python object. Returns None if not found.
    """
    cached = redis_client.get(key)
    if cached is None:
        return None
    if not isinstance(cached, str):
        return None  # or raise, but None is safest fallback
    try:
        return json.loads(cached)
    except Exception:
        return cached  # fallback if not JSON
