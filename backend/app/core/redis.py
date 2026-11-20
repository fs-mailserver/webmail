"""Shared async Redis client (Pub/Sub bus for realtime events in Phase 2)."""

from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True, socket_connect_timeout=5, socket_timeout=5, health_check_interval=30)


async def close_redis() -> None:
    if get_redis.cache_info().currsize:
        await get_redis().aclose()
        get_redis.cache_clear()
