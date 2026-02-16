import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.backend.utils import get_summary_card_data, get_realtime_online_count, load_member_stats, get_redis

async def debug():
    guild_id = -1771252136816
    print(f"DEBUGGING GUILD: {guild_id}")
    
    r = await get_redis()
    
    total_members_str = await r.get(f"presence:total:{guild_id}")
    print(f"REDISpresence:total:{guild_id} -> {total_members_str} (type: {type(total_members_str)})")
    
    online_count_str = await r.get(f"presence:online:{guild_id}")
    print(f"REDIS presence:online:{guild_id} -> {online_count_str}")
    
    summary = await get_summary_card_data(guild_id=guild_id)
    print(f"SUMMARY CARD DATA: {summary}")
    
    online = await get_realtime_online_count(guild_id=guild_id)
    print(f"REALTIME ONLINE: {online}")
    
    m_stats = await load_member_stats(guild_id=guild_id)
    print(f"MEMBER STATS TOTAL (last 5): {m_stats['total'][-5:] if 'total' in m_stats else 'N/A'}")

if __name__ == '__main__':
    asyncio.run(debug())
