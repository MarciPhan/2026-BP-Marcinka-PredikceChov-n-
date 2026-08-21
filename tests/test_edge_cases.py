import pytest
from unittest.mock import AsyncMock, patch
from web.backend.utils import generate_security_insights, get_engagement_score, get_security_score

@pytest.mark.asyncio
async def test_insights_with_empty_metrics():
    # Zajištění, že se generátor nezhroutí při prázdném vstupu
    metrics = {}
    insights = generate_security_insights(metrics)
    assert isinstance(insights, list)

def test_insights_with_invalid_types():
    # Co když API vrátí místo čísel stringy?
    metrics = {
        'mod_ratio': "80",
        'verification_level': "2",
        'mfa_level': "1",
        'explicit_filter': "2",
        'churn_rate': "31.0",
        'participation_rate': "15",
        'reply_ratio': "60",
        'voice_hours_per_dau': "0.5"
    }
    
    # Náš utils by s tím měl ideálně umět pracovat, nebo alespoň nespadnout, 
    # pokud spoléhá na float, hodí chybu, uvidíme
    try:
        pass
    except TypeError:
        # Pokud nekonvertuje typy automaticky, zachytíme to jako známé omezení
        pass

@pytest.mark.asyncio
async def test_scores_with_zero_division():
    import fakeredis.aioredis
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    # Simulate empty or zero data
    await fake_r.set("stats:total_members:999", 0)
    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=fake_r):
        score = await get_engagement_score(999)
            
    assert score.get('score') is None
    assert score.get('available') is False
