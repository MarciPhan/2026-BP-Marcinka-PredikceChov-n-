# Redis connection pooling
import os
import logging
import redis.asyncio as redis
import redis as redis_sync
from shared.config import settings

logger = logging.getLogger(__name__)

_pool = None  # global connection pool
_fake_redis = None
_fake_redis_sync = None

def _should_use_fakeredis() -> bool:
    if settings.environment == "test":
        return True
    if settings.environment == "development" and settings.use_fakeredis:
        return True
    return False

async def get_redis() -> redis.Redis:
    """Get Redis client from connection pool. Fails fast in production if offline."""
    global _pool, _fake_redis
    
    if _fake_redis is not None:
        return _fake_redis

    if _should_use_fakeredis():
        try:
            import fakeredis.aioredis
            _fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
            return _fake_redis
        except ImportError:
            logger.error("fakeredis not installed!")
            raise

    if _pool is None:
        _pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
        
    client = redis.Redis(connection_pool=_pool)
    try:
        await client.ping()
        return client
    except (redis.exceptions.ConnectionError, ConnectionRefusedError) as e:
        logger.error(f"Redis connection failed at {settings.redis_url}")
        raise RuntimeError(f"Service Unavailable: Redis connection failed. {e}")

async def get_redis_client() -> redis.Redis:
    """backwards compat alias"""
    return await get_redis()

def get_redis_sync() -> redis_sync.Redis:
    """Sync Redis client for maintenance scripts"""
    global _fake_redis_sync
    
    if _fake_redis_sync is not None:
        return _fake_redis_sync

    if _should_use_fakeredis():
        try:
            import fakeredis
            _fake_redis_sync = fakeredis.FakeRedis(decode_responses=True)
            return _fake_redis_sync
        except ImportError:
            raise

    client = redis_sync.from_url(settings.redis_url, decode_responses=True)
    try:
        client.ping()
        return client
    except (redis_sync.exceptions.ConnectionError, ConnectionRefusedError) as e:
        logger.error("Sync Redis connection failed.")
        raise RuntimeError(f"Service Unavailable: Sync Redis connection failed. {e}")
