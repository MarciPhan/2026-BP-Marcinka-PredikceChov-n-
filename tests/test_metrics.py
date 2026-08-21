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
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_security_score(999)
        
    assert isinstance(score, dict)
    assert 0 <= score.get('overall_score', -1) <= 100

@pytest.mark.asyncio
async def test_security_score_missing_data():
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_security_score(999)
        
    assert isinstance(score, dict)
    assert 0 <= score.get('overall_score', -1) <= 100
