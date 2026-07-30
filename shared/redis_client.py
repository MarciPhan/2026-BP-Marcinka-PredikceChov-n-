# Redis connection pooling
# TODO: maybe add connection retry logic?

import os
import logging
import redis.asyncio as redis
import redis as redis_sync

logger = logging.getLogger(__name__)

# default to localhost, override with REDIS_URL env var
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_pool = None  # global connection pool
_fake_redis = None
_fake_redis_sync = None

async def get_redis() -> redis.Redis:
    """Get Redis client from connection pool, fallback to fakeredis if offline"""
    global _pool, _fake_redis
    
    if _fake_redis is not None:
        return _fake_redis

    if _pool is None:
        _pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
        
    client = redis.Redis(connection_pool=_pool)
    try:
        await client.ping()
        return client
    except (redis.exceptions.ConnectionError, ConnectionRefusedError):
        logger.warning("Redis not available, falling back to FakeRedis")
        try:
            import fakeredis.aioredis
            _fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
            return _fake_redis
        except ImportError:
            logger.error("fakeredis not installed! Please run 'pip install fakeredis'")
            raise

async def get_redis_client() -> redis.Redis:
    """backwards compat alias"""
    return await get_redis()

def get_redis_sync() -> redis_sync.Redis:
    """Sync Redis client for maintenance scripts"""
    global _fake_redis_sync
    if _fake_redis_sync is not None:
        return _fake_redis_sync

    client = redis_sync.from_url(REDIS_URL, decode_responses=True)
    try:
        client.ping()
        return client
    except (redis_sync.exceptions.ConnectionError, ConnectionRefusedError):
        try:
            import fakeredis
            _fake_redis_sync = fakeredis.FakeRedis(decode_responses=True)
            return _fake_redis_sync
        except ImportError:
            raise
