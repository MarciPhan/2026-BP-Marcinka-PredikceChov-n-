import asyncio
import sys, os
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(""), "."))
sys.path.insert(0, ROOT_DIR)
from web.backend.repositories.redis_repo import RedisRepository
from web.backend.utils import get_summary_card_data

async def main():
    gid = -1771252136816
    sd = "2025-12-21"
    ed = "2026-01-20"
    repo = RedisRepository()
    
    m_stats = await repo.load_member_stats(gid, start_date=sd, end_date=ed)
    a_stats = await repo.get_activity_stats(gid, start_date=sd, end_date=ed)
    
    curr_total = m_stats["total"][-1] if m_stats.get("total") else 0
    curr_dau = a_stats["dau_data"][-1] if a_stats.get("dau_data") else 0
    
    sum_stats = await get_summary_card_data(discord_dau=curr_dau, discord_users=curr_total, guild_id=gid)
    
    print("member_stats total array len:", len(m_stats.get("total", [])))
    print("activity_stats DAU:", a_stats.get("avg_dau"))
    print("summary_stats users:", sum_stats["discord"]["users"])

asyncio.run(main())
