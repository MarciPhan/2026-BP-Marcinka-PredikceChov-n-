import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.main import on_guild_join, on_guild_remove

@pytest.mark.asyncio
@patch('bot.main.redis.from_url')
async def test_on_guild_join(mock_redis):
    # Mock redis instance
    mock_r = AsyncMock()
    mock_redis.return_value = mock_r
    
    # Mock guild
    mock_guild = MagicMock()
    mock_guild.id = 123456
    mock_guild.name = "Test Guild"
    
    # Mock subprocess for backfill to not actually run
    with patch('subprocess.Popen') as mock_popen:
        await on_guild_join(mock_guild)
        
        # Verify redis was called to add guild
        mock_r.sadd.assert_called()
        mock_r.close.assert_called()

@pytest.mark.asyncio
@patch('bot.main.redis.from_url')
async def test_on_guild_remove(mock_redis):
    # Mock redis instance
    mock_r = AsyncMock()
    mock_redis.return_value = mock_r
    
    # Mock guild
    mock_guild = MagicMock()
    mock_guild.id = 123456
    mock_guild.name = "Test Guild"
    
    await on_guild_remove(mock_guild)
    
    # Verify redis was called to remove guild
    mock_r.srem.assert_called()
    mock_r.close.assert_called()
