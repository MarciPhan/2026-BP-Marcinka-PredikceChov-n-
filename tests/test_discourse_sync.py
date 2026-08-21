import pytest
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from scripts.discourse_sync import DiscourseSync

class TestDiscourseSync(unittest.IsolatedAsyncioTestCase):

    @patch("scripts.discourse_sync.get_redis")
    @patch("httpx.AsyncClient.get")
    async def test_sync_guild_success(self, mock_get, mock_get_redis):
        # Setup Redis mock
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "url": "https://forum.example.com",
            "api_key": "test_key",
            "api_user": "admin_user"
        }
        mock_get_redis.return_value = mock_redis

        # Setup HTTP response mocks
        mock_latest_resp = MagicMock()
        mock_latest_resp.status_code = 200
        mock_latest_resp.json.return_value = {
            "topic_list": {
                "topics": [
                    {"id": 1, "title": "Test 1", "created_at": "2023-01-01T12:00:00Z", "like_count": 5},
                    {"id": 2, "title": "Test 2", "created_at": "2023-01-02T12:00:00Z", "like_count": 2}
                ]
            }
        }
    
        mock_get.return_value = mock_latest_resp
        
        mock_redis.sismember.return_value = False

        syncer = DiscourseSync()
        res = await syncer.sync_guild("guild123")
    
        self.assertTrue(res)
        mock_redis.incrby.assert_called_with("stats:total_msgs:guild123", 2)
        mock_redis.sadd.assert_any_call("discourse:synced_topics:guild123", "1")
        mock_redis.sadd.assert_any_call("discourse:synced_topics:guild123", "2")

    @patch("scripts.discourse_sync.get_redis")
    async def test_sync_guild_missing_config(self, mock_get_redis):
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {}
        mock_get_redis.return_value = mock_redis

        syncer = DiscourseSync()
        with self.assertRaises(ValueError):
            await syncer.sync_guild("guild_missing")

if __name__ == "__main__":
    unittest.main()
