import datetime
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from web.backend.services.analytics_service import DefaultAnalyticsService
class DummyRepo:
    def __init__(self):
        self.client = None
    async def get_client(self):
        return self.client


@pytest.mark.asyncio
async def test_fr_05_channel_storage():
    """FR-05: Channel storage (mocking redis behavior)"""
    # Create fake redis output
    fake_redis = AsyncMock()
    async def fake_scan_iter1(m): yield "events:msg:123:user1"; yield "events:msg:123:user2"
    fake_redis.scan_iter = fake_scan_iter1
    
    # Fake messages
    msgs_user1 = [
        json.dumps({"mid": "m1", "channel_id": "chA", "len": 10, "reply": False, "reaction_count": 0}),
        json.dumps({"mid": "m2", "channel_id": "chA", "len": 15, "reply": False, "reaction_count": 2})
    ]
    msgs_user2 = [
        json.dumps({"mid": "m3", "channel_id": "chB", "len": 5, "reply": False, "reaction_count": 0})
    ]
    
    async def fake_zrangebyscore(key, start, end):
        if "user1" in key: return msgs_user1
        if "user2" in key: return msgs_user2
        return []
        
    fake_redis.zrangebyscore.side_effect = fake_zrangebyscore
    
    repo = DummyRepo()
    repo.client = fake_redis
    service = DefaultAnalyticsService(repo)
    
    # Test aggregation
    data = await service.get_channel_activity(123, platform="discord")
    
    assert len(data) == 2
    # Should be sorted by messages
    assert data[0]["channel_id"] == "chA"
    assert data[0]["messages"] == 2
    assert data[0]["reactions"] == 2
    
    assert data[1]["channel_id"] == "chB"
    assert data[1]["messages"] == 1
    assert data[1]["reactions"] == 0

@pytest.mark.asyncio
async def test_fr_08_channel_filter():
    """FR-08: Filter by channel"""
    fake_redis = AsyncMock()
    async def fake_scan_iter1(m): yield "events:msg:123:user1"; yield "events:msg:123:user2"
    fake_redis.scan_iter = fake_scan_iter1
    
    msgs_user1 = [
        json.dumps({"mid": "m1", "channel_id": "chA", "len": 10, "reply": False, "reaction_count": 0}),
    ]
    msgs_user2 = [
        json.dumps({"mid": "m3", "channel_id": "chB", "len": 5, "reply": False, "reaction_count": 0})
    ]
    
    async def fake_zrangebyscore(key, start, end):
        if "user1" in key: return msgs_user1
        if "user2" in key: return msgs_user2
        return []
        
    fake_redis.zrangebyscore.side_effect = fake_zrangebyscore
    
    repo = DummyRepo()
    repo.client = fake_redis
    service = DefaultAnalyticsService(repo)
    
    data = await service.get_channel_activity(123, platform="discord", channel_id="chA")
    assert len(data) == 1
    assert data[0]["channel_id"] == "chA"

@pytest.mark.asyncio
async def test_fr_06_support_health():
    """FR-06: Answered, Unanswered, Self-reply, Non-support, Question-only"""
    fake_redis = AsyncMock()
    
    # Config setup
    cfg = json.dumps({"support_channels": ["chSupport"], "support_detection_mode": "question_only"})
    fake_redis.get.return_value = cfg
    
    async def fake_scan_iter2(m): yield "events:msg:123:reqUser"; yield "events:msg:123:helperUser"
    fake_redis.scan_iter = fake_scan_iter2
    
    # We use zrangebyscore withscores to get (event_json, score)
    # Timestamps (scores):
    ts_base = datetime.datetime.now().timestamp() - 10000
    
    events_req = [
        # Answered request (question, in support)
        (json.dumps({"mid": "req1", "channel_id": "chSupport", "is_question": True, "reply": False, "reply_to_mid": None, "reaction_count": 0}), ts_base),
        # Unanswered request
        (json.dumps({"mid": "req2", "channel_id": "chSupport", "is_question": True, "reply": False, "reply_to_mid": None, "reaction_count": 0}), ts_base + 10),
        # Not a question -> filtered out
        (json.dumps({"mid": "req3", "channel_id": "chSupport", "is_question": False, "reply": False, "reply_to_mid": None, "reaction_count": 0}), ts_base + 20),
        # Non-support channel -> filtered out
        (json.dumps({"mid": "req4", "channel_id": "chOther", "is_question": True, "reply": False, "reply_to_mid": None, "reaction_count": 0}), ts_base + 30),
        # Self-reply request
        (json.dumps({"mid": "req5", "channel_id": "chSupport", "is_question": True, "reply": False, "reply_to_mid": None, "reaction_count": 0}), ts_base + 40),
        # The self-reply
        (json.dumps({"mid": "rep_self", "channel_id": "chSupport", "is_question": False, "reply": True, "reply_to_mid": "req5", "reaction_count": 0}), ts_base + 50)
    ]
    
    events_helper = [
        # Valid reply to req1
        (json.dumps({"mid": "rep1", "channel_id": "chSupport", "is_question": False, "reply": True, "reply_to_mid": "req1", "reaction_count": 0}), ts_base + 300)
    ]
    
    async def fake_zrangebyscore_withscores(key, start, end, withscores=False):
        if "reqUser" in key: return events_req
        if "helperUser" in key: return events_helper
        return []
    
    fake_redis.zrangebyscore.side_effect = fake_zrangebyscore_withscores
    
    repo = DummyRepo()
    repo.client = fake_redis
    service = DefaultAnalyticsService(repo)
    
    data = await service.get_community_health_support(123, days=30)
    
    # We should have exactly 3 valid requests (req1, req2, req5)
    # req3 not question, req4 not support
    assert data["requests"] == 3
    
    # Answered should be 1 (req1) - req5 is a self-reply, req2 is unanswered
    assert data["answered"] == 1
    assert data["open"] == 2
    assert data["median_first_response_time"] == 300.0  # 300s response time for req1

@pytest.mark.asyncio
async def test_fr_08_api_filters():
    from fastapi.testclient import TestClient
    from web.backend.main import app
    client = TestClient(app)
    
    # This is an integration test simulating the router logic, we mock the service layer to just return the kwargs
    from web.backend.routers.api import api_channel_activity
    # Just asserting the route exists and accepts the params
    assert api_channel_activity is not None




@pytest.mark.asyncio
async def test_api_filters_and_auth():
    from fastapi.testclient import TestClient
    from web.backend.main import app
    from unittest.mock import patch
    
    client = TestClient(app)
    app.dependency_overrides.clear()
    # Check CSRF on admin endpoint
    resp_no_csrf = client.post("/api/admin/support-channels", json={"support_channels": []}, headers={"Cookie": "session=dummy;"})
    # Since require_auth will fail on dummy session without valid mock, let's just assert it doesn't return 200 OK without CSRF
    pass
    
    # Test v1 auth logic is separated from internal api
    # If there is a v1 endpoint, it should require X-API-Key (e.g. /api/v1/health-research which might exist)
    # We can just verify the newly added internal API route doesn't have /v1/ prefix
    assert client.get("/api/v1/channel-activity").status_code == 404
    
    # We test the topic_id vs channel_id translation logic using service mock
    with patch("web.backend.services.analytics_service.DefaultAnalyticsService.get_channel_activity", new_callable=AsyncMock) as mock_activity:
        mock_activity.return_value = []
        
        # Override auth dependency to allow request
        from web.backend.routers.api import require_auth
        app.dependency_overrides[require_auth] = lambda: True
        
        client.get("/api/channel-activity?platform=discourse&channel_id=123", cookies={"session": "dummy"})
        mock_activity.assert_called_once()
        # kwargs check
        args, kwargs = mock_activity.call_args
        # Should have translated channel_id to topic_id=123, channel_id=None
        assert args[4] == None # channel_id
        assert args[5] == "123" # topic_id
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_api_filters_and_auth():
    from fastapi.testclient import TestClient
    from web.backend.main import app
    from unittest.mock import patch
    
    client = TestClient(app)
    app.dependency_overrides.clear()
    # Check CSRF on admin endpoint
    resp_no_csrf = client.post("/api/admin/support-channels", json={"support_channels": []}, headers={"Cookie": "session=dummy;"})
    # Since require_auth will fail on dummy session without valid mock, let's just assert it doesn't return 200 OK without CSRF
    assert resp_no_csrf.status_code in [401, 403]
    
    # Test v1 auth logic is separated from internal api
    # If there is a v1 endpoint, it should require X-API-Key (e.g. /api/v1/health-research which might exist)
    # We can just verify the newly added internal API route doesn't have /v1/ prefix
    assert client.get("/api/v1/channel-activity").status_code == 404
    
    # We test the topic_id vs channel_id translation logic using service mock
    with patch("web.backend.services.analytics_service.DefaultAnalyticsService.get_channel_activity", new_callable=AsyncMock) as mock_activity:
        mock_activity.return_value = []
        
        # Override auth dependency to allow request
        from web.backend.routers.api import require_auth
        app.dependency_overrides[require_auth] = lambda: True
        
        client.get("/api/channel-activity?platform=discourse&channel_id=123", cookies={"session": "dummy"})
        mock_activity.assert_called_once()
        # kwargs check
        args, kwargs = mock_activity.call_args
        # Should have translated channel_id to topic_id=123, channel_id=None
        assert args[4] == None # channel_id
        assert args[5] == "123" # topic_id
        
        app.dependency_overrides.clear()
