import pytest
import ipaddress
import socket
from unittest.mock import patch, MagicMock

# 1. Idempotence Discourse Konektoru
@pytest.mark.asyncio
async def test_discourse_idempotency():
    # Zde bychom ideálně volali skutečný DiscourseSync.sync_guild
    # Pro účely BP simulujeme chování (pokud nelze importovat).
    from scripts.discourse_sync import DiscourseSync
    from shared.config import settings
    
    # We create a mock redis to test idempotency
    import fakeredis.aioredis
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    
    syncer = DiscourseSync(redis_client=fake_r)
    
    # Simulate first import
    guild_id = "test-guild"
    await fake_r.hset(f"discourse:conf:{guild_id}", mapping={"url": "http://fake", "api_key": "fake", "api_user": "fake"})
    
    # Simulate processing a topic twice
    topic_data = {"id": 123, "title": "Test Topic", "created_at": "2024-01-01T12:00:00.000Z"}
    
    # Pass 1
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"topic_list": {"topics": [topic_data]}}
        mock_get.return_value = mock_response
        
        await syncer.sync_guild(guild_id)
        
    count1 = await fake_r.zcard(f"events:msg:{guild_id}:discourse")
    
    # Pass 2
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"topic_list": {"topics": [topic_data]}}
        mock_get.return_value = mock_response
        
        await syncer.sync_guild(guild_id)
        
    count2 = await fake_r.zcard(f"events:msg:{guild_id}:discourse")
    
    # Assert Idempotency: Count should remain the same (no duplicates)
    assert count1 == count2
    assert count1 > 0

# 2. Ošetření SSRF v konfigurátoru
@pytest.mark.asyncio
async def test_ssrf_protection():
    # Testujeme logiku SSRF
    from web.backend.routers.api import api_add_discourse
    from fastapi import Request
    
    request = MagicMock(spec=Request)
    request.session = {"authenticated": True, "discord_user": {"id": "123"}, "csrf_token": "valid"}
    
    # Localhost attack
    resp = await api_add_discourse(request, url="http://127.0.0.1", api_key="a", api_user="b", csrf_token="valid")
    assert resp.status_code == 403
    
    # AWS metadata attack
    resp = await api_add_discourse(request, url="http://169.254.169.254", api_key="a", api_user="b", csrf_token="valid")
    assert resp.status_code == 403
    
    # Private IP attack
    resp = await api_add_discourse(request, url="http://10.0.0.5", api_key="a", api_user="b", csrf_token="valid")
    assert resp.status_code == 403

# 3. Správnost Engagement Score podle nového vzorce
@pytest.mark.asyncio
async def test_engagement_score_formula():
    from web.backend.services.analytics_service import DefaultAnalyticsService
    from web.backend.repositories.redis_repo import RedisRepository
    import fakeredis.aioredis
    
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repo = RedisRepository()
    repo.get_client = MagicMock(return_value=fake_r)
    
    svc = DefaultAnalyticsService(repo)
    guild_id = 999
    
    import datetime
    now_ts = datetime.datetime.now().timestamp()
    
    # Prepare data for 10 users, 2 DAU, 10 msgs, 20 reactions
    await fake_r.set(f"stats:total_members:{guild_id}", 10)
    d_str = datetime.datetime.now().strftime("%Y%m%d")
    d_str_hyphen = datetime.datetime.now().strftime("%Y-%m-%d")
    await fake_r.pfadd(f"hll:dau:{guild_id}:{d_str}", "u1", "u2") # 2 DAU
    
    # 10 messages, 20 reactions
    import json
    for i in range(10):
        await fake_r.zadd(f"events:msg:{guild_id}:u1", {json.dumps({"id": i, "reaction_count": 2}): now_ts})
        
    score_data = await svc.get_engagement_score(guild_id, start_date=d_str_hyphen, end_date=d_str_hyphen)
    
    # S_eng = 100 * (w_u*U + w_m*M + w_r*R + w_v*V) / sum(w)
    # V is missing, so w_v is excluded.
    # U = 2/10 = 0.2 -> normalized: 0.2 / 0.25 = 0.8
    # M = 10 / (2 * 1) = 5 -> normalized: 5 / 5.0 = 1.0
    # R = 20 / 10 = 2 -> normalized: 2 / 2.0 = 1.0
    # Expected components: u=80, m=100, r=100
    # Overall score: (80 + 100 + 100) / 3 = 93.33 -> 93
    
    assert score_data["components"]["users"]["value"] == 80
    assert score_data["components"]["messages"]["value"] == 100
    assert score_data["components"]["reactions"]["value"] == 100
    assert not score_data["components"]["voice"]["available"] # V should be excluded
    assert score_data["score"] == 93
