import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# Fix import path for testing
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from web.backend.routers.api import api_add_discourse
from shared.redis_client import get_redis

@pytest.mark.asyncio
async def test_ssrf_protection_discourse_api():
    """
    Testujeme, že endpoint pro přidání Discourse fóra
    správně blokuje SSRF útoky na lokální a privátní IP.
    """
    request = MagicMock()
    request.session = {"discord_user": {"id": "123", "username": "test"}}
    
    # 1. Test localhost IPv4
    response_lh = await api_add_discourse(
        request=request, 
        url="http://127.0.0.1", 
        api_key="test", 
        api_user="test"
    )
    assert isinstance(response_lh, JSONResponse)
    assert response_lh.status_code == 403
    import json
    data_lh = json.loads(response_lh.body.decode())
    assert "SSRF Protection" in data_lh.get("error", "")
    
    # 2. Test metadata server IP (AWS)
    response_meta = await api_add_discourse(
        request=request, 
        url="http://169.254.169.254", 
        api_key="test", 
        api_user="test"
    )
    assert response_meta.status_code == 403
    data_meta = json.loads(response_meta.body.decode())
    assert "SSRF Protection" in data_meta.get("error", "")
    
    # 3. Test Invalid Scheme (např. file://)
    response_file = await api_add_discourse(
        request=request,
        url="file:///etc/passwd",
        api_key="test",
        api_user="test"
    )
    assert response_file.status_code == 400

@pytest.mark.asyncio
async def test_data_flow_event_redis_api():
    """
    Simulace toku dat: událost -> zápis do Redis -> API metrika
    Tím testujeme, že zpracování reálných dat funguje konzistentně.
    """
    # Použijeme mock pro get_redis, abychom otestovali logiku z pohledu API/funkce,
    # nebo zapíšeme data a načteme je.
    # Protože v testech máme přístup k funkci get_engagement_score atd. z utils:
    from web.backend.utils import get_engagement_score
    
    mock_redis = AsyncMock()
    mock_redis.hgetall.return_value = {}
    async def mock_get_func(k):
        return b"2000" if "mau" in k else b"100"
    mock_redis.get = mock_get_func
    mock_redis.pfcount.return_value = 50
    
    # mock zrangebyscore to return some fake voice/message data
    mock_redis.zrangebyscore.return_value = ['{"duration": 3600}', '{"reply": true}']
    
    # Vracíme iterátor pro scan_iter
    async def mock_scan_iter(match):
        yield f"{match.replace(':*', ':1')}"
    mock_redis.scan_iter = mock_scan_iter

    with patch('web.backend.core.container.AppContainer.repo.get_client', return_value=mock_redis):
        # analytics_service expects guild_id as first param
        score = await get_engagement_score(123456)
        
    assert score is not None
    assert "score" in score
    assert isinstance(score["score"], (int, float))
    assert score["score"] > 0
