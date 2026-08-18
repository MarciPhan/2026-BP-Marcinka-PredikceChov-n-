import pytest
from unittest.mock import AsyncMock, patch
from web.backend.utils import get_engagement_score, get_security_score, get_trend_analysis

@pytest.mark.asyncio
async def test_engagement_score():
    data = {
        'avg_dau': 100,
        'mau': 500,
        'participation_rate': 20,
        'reply_ratio': 50,
        'voice_hours_per_dau': 1.5,
        'retention_7d': 40
    }
    mock_r = AsyncMock()
    mock_r.hgetall.return_value = {}
    
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=mock_r):
        score = await get_engagement_score(data)
            
    assert isinstance(score, dict)
    assert 0 <= score.get('score', 0) <= 100

@pytest.mark.asyncio
async def test_engagement_score_missing_data():
    data = {}
    mock_r = AsyncMock()
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=mock_r):
        score = await get_engagement_score(data)
            
    assert score.get('score', -1) == 0.0

@pytest.mark.asyncio
async def test_security_score():
    data = {
        'mod_ratio': 15,
        'users_per_mod': 100,
        'verification_level': 3,
        'mfa_level': 1,
        'explicit_filter': 2
    }
    mock_r = AsyncMock()
    mock_r.hgetall.return_value = {}
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=mock_r):
        score = await get_security_score(data)
        
    assert isinstance(score, dict)
    assert 0 <= score.get('overall_score', 0) <= 100

@pytest.mark.asyncio
async def test_security_score_missing_data():
    data = {}
    mock_r = AsyncMock()
    mock_r.hgetall.return_value = {}
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=mock_r):
        score = await get_security_score(data)
        
    # Default behavior when data is missing might give some base score
    assert isinstance(score, dict)
    assert 0 <= score.get('overall_score', 0) <= 100
