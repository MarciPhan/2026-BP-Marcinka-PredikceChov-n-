# Redis connection pooling
# TODO: maybe add connection retry logic?

import os
import redis.asyncio as redis

# default to localhost, override with REDIS_URL env var
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_pool = None  # global connection pool

async def get_redis() -> redis.Redis:
    """Get Redis client from connection pool"""
    global _pool
    if _pool is None:
        # lazy init pool on first use
        _pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
    return redis.Redis(connection_pool=_pool)

async def get_redis_client() -> redis.Redis:
    """backwards compat alias"""
    return await get_redis()

def get_redis_sync() -> redis.Redis:
    """Sync Redis client for maintenance scripts"""
    return redis.from_url(REDIS_URL, decode_responses=True)
