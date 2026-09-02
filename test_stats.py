import asyncio
import json
from web.backend.repositories.redis_repo import RedisRepository

async def main():
    repo = RedisRepository()
    stats = await repo.get_deep_stats_redis(615171377783242769, '2026-08-03', '2026-09-02')
    print(json.dumps(stats, indent=2))

asyncio.run(main())
