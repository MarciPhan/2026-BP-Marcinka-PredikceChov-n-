import pytest
from unittest.mock import AsyncMock, patch
from web.backend.utils import get_engagement_score, get_security_score, get_trend_analysis
import fakeredis.aioredis

@pytest.mark.asyncio
async def test_engagement_score():
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await fake_r.set("stats:total_members:999", 100)
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_engagement_score(999)
            
    assert isinstance(score, dict)
    assert score.get("available") is True
    assert 0 <= score.get('score', -1) <= 100

@pytest.mark.asyncio
async def test_engagement_score_missing_data():
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_engagement_score(999)
            
    assert score.get("available") is False

@pytest.mark.asyncio
async def test_security_score():
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await fake_r.hset("config:security_weights", mapping={
        "mod_ratio": "25", "security": "25", "engagement": "25", "moderation": "25"
    })
    await fake_r.hset("config:security_ideals", mapping={
        "mod_ratio_min": "50", "mod_ratio_max": "100",
        "verification_level": "2", "dau_percent": "10",
        "mod_actions_min": "1", "mod_actions_max": "5"
    })
    await fake_r.set("stats:total_members:999", 500)
    await fake_r.set("stats:mod_count:999", 10)
    
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_security_score(999)
        
    assert isinstance(score, dict)
    assert 0 <= score.get('overall_score', -1) <= 100

@pytest.mark.asyncio
async def test_security_score_missing_data():
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_security_score(999)
        
    assert score.get('overall_score') is None
    assert score.get('available') is False
