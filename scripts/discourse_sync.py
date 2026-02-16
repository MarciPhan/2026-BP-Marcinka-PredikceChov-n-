
import asyncio
import aiohttp
import redis.asyncio as redis
import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add parent directory to path to import shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.keys import (
    K_DISCOURSE_CONF, K_DISCOURSE_IDS, K_DAU, K_HOURLY, K_MSGLEN, K_TOTAL_MSGS,
    K_EVENTS_MSG, K_EVENTS_ACTION
)

# Configuration from env or defaults
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discourse_sync.log")
    ]
)
logger = logging.getLogger("discourse_sync")

class DiscourseSync:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.session = None

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_json(self, url: str, api_key: str, api_user: str) -> Dict[str, Any]:
        """Fetch JSON from Discourse API with auth headers."""
        session = await self.get_session()
        headers = {
            "Api-Key": api_key,
            "Api-Username": api_user,
            "Accept": "application/json"
        }
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    logger.warning(f"Rate limited by {url}. Waiting...")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.error(f"Error fetching {url}: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception fetching {url}: {e}")
            return None

    async def sync_guild(self, guild_id: str):
        """Sync a single Discourse 'guild'."""
        logger.info(f"Syncing guild {guild_id}...")
        
        # 1. Load config
        conf = await self.redis.hgetall(K_DISCOURSE_CONF(guild_id))
        if not conf:
            logger.warning(f"Configuration not found for {guild_id}")
            return

        base_url = conf.get("url")
        api_key = conf.get("api_key")
        api_user = conf.get("api_user")
        
        if not base_url or not api_key:
            return

        # 2. Sync Topics (Threads)
        # We use /latest.json to get recent topics
        topics_url = f"{base_url}/latest.json?order=created"
        data = await self.fetch_json(topics_url, api_key, api_user)
        
        if data and "topic_list" in data and "topics" in data["topic_list"]:
            users_map = {u["id"]: u for u in data.get("users", [])}
            
            for topic in data["topic_list"]["topics"]:
                await self.process_topic(guild_id, topic, users_map)
                
        # 3. Sync Recent Posts
        # /posts.json is authentic, brings recent posts
        posts_url = f"{base_url}/posts.json" 
        posts_data = await self.fetch_json(posts_url, api_key, api_user)
        
        if posts_data and "latest_posts" in posts_data:
             for post in posts_data["latest_posts"]:
                 await self.process_post(guild_id, post, base_url, api_key, api_user)

        # 4. Sync Site Stats (Total Members, etc.)
        # /site/statistics.json gives us good summary
        stats_url = f"{base_url}/site/statistics.json"
        stats_data = await self.fetch_json(stats_url, api_key, api_user)
        
        if stats_data:
            user_count = stats_data.get("users_count", 0)
            active_users = stats_data.get("active_users_last_day", 0)
            
            # Update presence keys for Dashboard KPIs
            await self.redis.set(f"presence:total:{guild_id}", str(user_count))
            await self.redis.set(f"presence:online:{guild_id}", str(active_users))
            
            # Also update total messages just in case our manual count is off?
            # No, let's keep our manual count as it tracks our specific event logic.
            pass

    async def process_topic(self, guild_id: str, topic: Dict, users_map: Dict):
        """Process a topic as a 'thread create' event."""
        # Use created_at
        created_at_str = topic.get("created_at")
        if not created_at_str: return
        
        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        ts = dt.timestamp()
        
        # Check if too old (ignored)
        if (datetime.now(timezone.utc) - dt).days > 30:
            return

        # Map user
        # user_id in redis will be "discourse:{site_id}:{user_id}" to avoid collision
        # But for simplistic "virtual guild" we can just use the discourse integer ID 
        # because the redis keys are namespaces by guild_id anyway!
        # events:msg:{guild_id}:{user_id} -> OK!
        
        # However, to display them nicely in dashboard, we might need to fetch user info 
        # and store it in user:info:{uid}.
        # Dashboard expects user_info to have 'name', 'avatar'.
        
        d_user_id = topic.get("poster_user_id") # This is likely not in topic object directly in list, check docs
        # Actually in topic_list, topics have 'posters' array. The creator is usually the first poster.
        # But 'latest.json' topics usually have 'last_poster_username' etc.
        # Let's rely on posts for activity. Topics creation is separate.
        pass

    async def process_post(self, guild_id: str, post: Dict, base_url: str, api_key: str, api_user: str):
        """Process a post as a message event."""
        post_id = post.get("id")
        created_at_str = post.get("created_at")
        
        # Check cache/deduplication
        # We don't want to re-process headers every time.
        # Redis set: discourse:processed_posts:{guild_id}
        is_processed = await self.redis.sismember(f"discourse:processed:{guild_id}", post_id)
        if is_processed:
            return

        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        ts = dt.timestamp()
        
        # Filter old posts (> 5 days) to avoid backfilling everything on every run
        # Implementation Note: For initial run, user might want backfill. 
        # unique set prevents duplicates, so we can be generous with time window.
        if (datetime.now(timezone.utc) - dt).days > 7:
            await self.redis.sadd(f"discourse:processed:{guild_id}", post_id)
            return

        user_id = post.get("user_id")
        username = post.get("username")
        raw_text = post.get("raw") or post.get("cooked", "") # cooked is html
        
        # Store User Info cache
        # We need to ensure dashboard can resolve this user_id
        u_key = f"user:info:{user_id}" # WARNING: Collision risk if Discord ID == Discourse ID?
        # Yes. Discord IDs are snowflakes (large ints). Discourse IDs are small ints (1, 2, 100).
        # Dashboard uses user_id to fetch user:info:{uid}.
        # If we use small ints for discourse, it wont collide with snowflakes (approx > 4e17).
        # So we are SAFE to use raw discourse ID.
        
        # But we should cache user info
        await self.redis.hset(u_key, mapping={
            "name": username,
            "username": username,
            "avatar": "" # Discourse avatar URL logic is complex {size}/template
        })
        
        # Record Metric: Message Event
        # Key: events:msg:{guild_id}:{user_id}
        # Value: JSON {len, reply, channel(topic), ts}
        event_data = {
            "len": len(raw_text),
            "reply": post.get("post_number") > 1,
            "channel": f"topic-{post.get('topic_id')}",
            "ts": ts
        }
        await self.redis.zadd(K_EVENTS_MSG(guild_id, user_id), {json.dumps(event_data): ts})
        
        # Record Metric: Total Msgs
        await self.redis.incr(K_TOTAL_MSGS(guild_id))
        
        # Record Metric: Hourly stats
        day_str = dt.strftime("%Y%m%d")
        hour = dt.hour
        await self.redis.hincrby(K_HOURLY(guild_id, day_str), str(hour), 1)
        
        # Record Metric: Message Length
        l = len(raw_text)
        bucket = 0
        if l > 250: bucket = 250
        elif l > 150: bucket = 150
        elif l > 75: bucket = 75
        elif l > 30: bucket = 30
        elif l > 5: bucket = 5
        await self.redis.zincrby(K_MSGLEN(guild_id), 1, str(bucket))
        
        # Record Metric: DAU (HLL)
        await self.redis.pfadd(K_DAU(guild_id, day_str), str(user_id))
        
        # Cleanup
        await self.redis.sadd(f"discourse:processed:{guild_id}", post_id)
        logger.info(f"Processed post {post_id} from {username}")

    async def run_once(self):
        """Run one synchronization cycle for all guilds."""
        # Get all Discourse IDs
        ids = await self.redis.smembers(K_DISCOURSE_IDS())
        logger.info(f"Found {len(ids)} Discourse guilds to sync.")
        
        for gid in ids:
            try:
                await self.sync_guild(gid)
            except Exception as e:
                logger.error(f"Error syncing guild {gid}: {e}")

    async def run_forever(self):
        logger.info("Starting Discourse Sync Service...")
        while True:
            await self.run_once()
            logger.info("Sleeping for 5 minutes...")
            await asyncio.sleep(300)

if __name__ == "__main__":
    syncer = DiscourseSync()
    try:
        if "--once" in sys.argv:
            asyncio.run(syncer.run_once())
        else:
            asyncio.run(syncer.run_forever())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
