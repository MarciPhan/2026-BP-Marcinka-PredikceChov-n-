import httpx
import asyncio
import time
from typing import Dict, Any

from utils import get_redis_client

class DiscourseSync:
    def __init__(self):
        pass

    async def sync_guild(self, guild_id: str):
        r = await get_redis_client()
        conf_key = f"discourse:conf:{guild_id}"
        config = await r.hgetall(conf_key)
        
        if not config or "url" not in config:
            raise ValueError(f"No discourse configuration found for guild {guild_id}")
            
        url = config["url"]
        api_key = config.get("api_key")
        api_user = config.get("api_user")
        
        headers = {
            "Api-Key": api_key,
            "Api-Username": api_user
        }
        
        async with httpx.AsyncClient() as client:
            # Basic sync: fetch latest topics and posts
            # In a real scenario, this would use pagination and handle rate limits
            try:
                resp = await client.get(f"{url}/latest.json", headers=headers)
                if resp.status_code != 200:
                    raise Exception(f"Failed to fetch latest topics: {resp.status_code}")
                    
                data = resp.json()
                topics = data.get("topic_list", {}).get("topics", [])
                
                for topic in topics:
                    # Mark activity
                    await self._record_activity(r, guild_id, "discourse_topic", topic)
                    
            except Exception as e:
                print(f"Error syncing discourse for {guild_id}: {e}")
                raise e

    async def _record_activity(self, r, guild_id: str, event_type: str, data: Dict[str, Any]):
        # Store a minimal representation of the event to Redis
        timestamp = int(time.time() * 1000)
        event_id = f"{event_type}:{data.get('id', timestamp)}"
        
        # Minimal data payload 
        event_data = {
            "platform": "discourse",
            "type": event_type,
            "id": str(data.get("id")),
            "title": data.get("title", ""),
            "created_at": data.get("created_at", ""),
            "timestamp": str(timestamp)
        }
        
        await r.hset(f"events:{guild_id}:{event_id}", mapping=event_data)
        
        # Add to hourly stats (simple daily/hourly activity counter)
        import datetime
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        hour_str = now.strftime("%H")
        
        await r.hincrby(f"stats:hourly:{guild_id}:{date_str}", hour_str, 1)
        
        # Also increment total stats
        await r.incr(f"stats:total_events:{guild_id}")
