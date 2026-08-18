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
        mock_site_resp = MagicMock()
        mock_site_resp.status_code = 200

        mock_about_resp = MagicMock()
        mock_about_resp.status_code = 200
        mock_about_resp.json.return_value = {
            "about": {
                "stats": {
                    "topic_count": 150,
                    "post_count": 1200,
                    "user_count": 450,
                    "active_users_7_days": 70
                }
            }
        }

        mock_get.side_effect = [mock_site_resp, mock_about_resp]

        syncer = DiscourseSync()
        res = await syncer.sync_guild("guild123")

        self.assertTrue(res)
        mock_redis.set.assert_any_call("presence:total:guild123", 450)
        mock_redis.set.assert_any_call("stats:total_msgs:guild123", 1200)

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
