import pytest
import fakeredis.aioredis
from shared.redis_client import get_redis_client
import json

@pytest.fixture
async def mock_redis():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.close()

@pytest.mark.asyncio
async def test_redis_set_get(mock_redis):
    await mock_redis.set("test_key", "test_value")
    value = await mock_redis.get("test_key")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_redis_json_data(mock_redis):
    data = {"users": 100, "active": 50}
    await mock_redis.set("stats_123", json.dumps(data))
    
    raw_data = await mock_redis.get("stats_123")
    parsed_data = json.loads(raw_data)
    assert parsed_data["users"] == 100
    assert parsed_data["active"] == 50

@pytest.mark.asyncio
async def test_redis_delete(mock_redis):
    await mock_redis.set("temp_key", "temp")
    assert await mock_redis.get("temp_key") == "temp"
    
    await mock_redis.delete("temp_key")
    assert await mock_redis.get("temp_key") is None
