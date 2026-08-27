import redis

from src.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis_client
