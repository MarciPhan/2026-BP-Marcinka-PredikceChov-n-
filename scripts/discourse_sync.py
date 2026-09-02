import asyncio
import httpx
import time
import json
import argparse
import sys
import os
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.redis_client import get_redis

class DiscourseSync:
    """
    Konektor pro synchronizaci dat z Discourse fóra do CommunityMetrics databáze.
    Tato třída slouží k integraci událostí (témata, příspěvky) z externího fóra.
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client

    async def process_topic(self, r, guild_id, topic, pipe):
        t_id = str(topic.get("id"))
        
        created_at_str = topic.get("created_at")
        try:
            dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except:
            dt = datetime.now(timezone.utc)
            
        ts = dt.timestamp()
        
        event_data = {
            "id": t_id,
            "title": topic.get("title"),
            "source": "discourse",
            "reaction_count": topic.get("like_count", 0)
        }
        
        pipe.zadd(f"events:msg:{guild_id}:discourse", {json.dumps(event_data): ts})
        
        posters = topic.get("posters", [])
        uid = str(posters[0].get("user_id", "0")) if posters else "0"
        d_str = dt.strftime("%Y%m%d")
        hour = dt.hour
        weekday = dt.weekday()
        msg_len = len(topic.get("title", ""))
        
        if msg_len == 0: bucket = 0
        elif msg_len <= 10: bucket = 5
        elif msg_len <= 50: bucket = 30
        elif msg_len <= 100: bucket = 75
        elif msg_len <= 200: bucket = 150
        else: bucket = 250
        
        pipe.pfadd(f"hll:dau:{guild_id}:{d_str}", str(uid))
        pipe.hincrby(f"stats:hourly:{guild_id}:{d_str}", hour, 1)
        pipe.hincrby(f"stats:heatmap:{guild_id}", f"{weekday}_{hour}", 1)
        pipe.zincrby(f"stats:msglen:{guild_id}", 1, bucket)
        pipe.incr(f"stats:total_msgs:{guild_id}")
        
        category_id = str(topic.get("category_id", "0"))
        pipe.incr(f"stats:channel:{guild_id}:{category_id}:{d_str}")
        pipe.zincrby(f"stats:channel_total:{guild_id}", 1, category_id)
        pipe.zincrby(f"leaderboard:messages:{guild_id}", 1, str(uid))
        pipe.zincrby(f"stats:user_daily:{guild_id}:{d_str}", 1, str(uid))
        pipe.lpush(f"leaderboard:msg_lengths:{guild_id}:{uid}", msg_len)
        pipe.ltrim(f"leaderboard:msg_lengths:{guild_id}:{uid}", 0, 99)
        pipe.hincrby(f"stats:channel_hourly:{guild_id}:{category_id}", hour, 1)
        pipe.hset(f"channel:info:{category_id}", mapping={"name": f"Kategorie {category_id}", "guild_id": str(guild_id)})
        
    async def sync_guild(self, guild_id: str):
        """
        Provede synchronizaci fóra se zadaným ID.
        Stahuje témata přes Discourse API a idempotně je ukládá.
        """
        r = self.redis_client or await get_redis()
        try:
            conf = await r.hgetall(f"discourse:conf:{guild_id}")
            if not conf:
                raise ValueError("Konfigurace Discourse fóra nenalezena.")
                
            url = conf.get("url")
            api_key = conf.get("api_key")
            api_user = conf.get("api_user")
            
            if not url or not api_key or not api_user:
                raise ValueError("Neúplná konfigurace API klíčů.")
                
            headers = {
                "Api-Key": api_key,
                "Api-Username": api_user
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    about_resp = await client.get(f"{url}/about.json", headers=headers)
                    if about_resp.status_code == 200:
                        about_data = about_resp.json()
                        users_count = about_data.get("about", {}).get("stats", {}).get("users_count")
                        if users_count:
                            await r.set(f"presence:total:{guild_id}", users_count)
                            await r.set(f"stats:total_members:{guild_id}", users_count)
                except Exception as e:
                    print(f"Nepodařilo se získat počet členů z about.json: {e}")

                # Načtení topics (latest)
                topics_resp = await client.get(f"{url}/latest.json", headers=headers)
                if topics_resp.status_code != 200:
                    raise Exception(f"Chyba při komunikaci s Discourse API: {topics_resp.status_code}")
                    
                topics_data = topics_resp.json()
                topics = topics_data.get("topic_list", {}).get("topics", [])
                
                # Zpracování témat idempotně
                synced_set_key = f"discourse:synced_topics:{guild_id}"
                new_msgs = 0
                
                pipe = r.pipeline()
                for topic in topics:
                    t_id = str(topic.get("id"))
                    
                    # Idempotence: Zkontrolujeme, zda už jsme toto téma zpracovali
                    is_member = await r.sismember(synced_set_key, t_id)
                    if is_member:
                        continue
                        
                    # Přidáme do setu zpracovaných
                    pipe.sadd(synced_set_key, t_id)
                    await self.process_topic(r, guild_id, topic, pipe)
                    new_msgs += 1
                    
                if new_msgs > 0:
                    from shared.config import settings
                    cutoff = time.time() - (settings.event_retention_days * 86400)
                    pipe.zremrangebyscore(f"events:msg:{guild_id}:discourse", "-inf", cutoff)
                    await pipe.execute()
                    
                return True
                
        except Exception as e:
            print(f"Chyba při synchronizaci Discourse (ID: {guild_id}): {e}")
            raise e
        finally:
            if not self.redis_client:
                await r.close()

    async def backfill_guild(self, guild_id: str):
        """
        Backfill pro Discourse fórum (stránkuje přes latest.json).
        """
        r = self.redis_client or await get_redis()
        try:
            await r.hset(f"backfill:status:{guild_id}", mapping={
                "status": "processing",
                "total_messages": 0,
                "current_channel": "připojování k Discourse"
            })
            
            conf = await r.hgetall(f"discourse:conf:{guild_id}")
            if not conf:
                await r.hset(f"backfill:status:{guild_id}", mapping={"status": "error", "message": "Konfigurace fóra nenalezena."})
                return
                
            url = conf.get("url")
            api_key = conf.get("api_key")
            api_user = conf.get("api_user")
            
            headers = {"Api-Key": api_key, "Api-Username": api_user}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    about_resp = await client.get(f"{url}/about.json", headers=headers)
                    if about_resp.status_code == 200:
                        about_data = about_resp.json()
                        users_count = about_data.get("about", {}).get("stats", {}).get("users_count")
                        if users_count:
                            await r.set(f"presence:total:{guild_id}", users_count)
                            await r.set(f"stats:total_members:{guild_id}", users_count)
                except Exception as e:
                    print(f"Nepodařilo se získat počet členů z about.json: {e}")

                page = 0
                total_processed = 0
                synced_set_key = f"discourse:synced_topics:{guild_id}"
                
                while True:
                    await r.hset(f"backfill:status:{guild_id}", "current_channel", f"zpracovávám stranu {page}")
                    resp = await client.get(f"{url}/latest.json?no_definitions=true&page={page}", headers=headers)
                    if resp.status_code != 200:
                        if page == 0:
                            raise Exception(f"Chyba při komunikaci s API (kód {resp.status_code}): {resp.text}")
                        break
                        
                    data = resp.json()
                    topics = data.get("topic_list", {}).get("topics", [])
                    if not topics:
                        break
                        
                    pipe = r.pipeline()
                    processed_in_page = 0
                    for topic in topics:
                        t_id = str(topic.get("id"))
                        is_member = await r.sismember(synced_set_key, t_id)
                        if is_member:
                            continue
                            
                        pipe.sadd(synced_set_key, t_id)
                        await self.process_topic(r, guild_id, topic, pipe)
                        processed_in_page += 1
                        total_processed += 1
                    
                    if processed_in_page > 0:
                        await pipe.execute()
                        await r.hset(f"backfill:status:{guild_id}", "total_messages", total_processed)
                    
                    # Discourse limits pages usually or returns 404/empty. Let's break after 1000 pages to be safe.
                    page += 1
                    if page > 1000:
                        break
                    await asyncio.sleep(0.5) # rate limit prevention
                    
            await r.hset(f"backfill:status:{guild_id}", mapping={
                "status": "completed",
                "total_messages": total_processed,
                "current_channel": "hotovo"
            })
            print(f"Backfill fóra {guild_id} úspěšně dokončen. Staženo {total_processed} nových témat.")
        except Exception as e:
            print(f"Chyba při backfillu Discourse (ID: {guild_id}): {e}")
            await r.hset(f"backfill:status:{guild_id}", mapping={"status": "error", "message": str(e)})
        finally:
            if not self.redis_client:
                await r.close()

    async def sync_all(self):
        """
        Synchronizuje všechna nakonfigurovaná Discourse fóra uložená v databázi Redis.
        """
        r = await get_redis()
        try:
            guild_ids = await r.smembers("discourse:ids")
            if not guild_ids:
                return
            for gid in guild_ids:
                try:
                    await self.sync_guild(gid)
                except Exception as e:
                    print(f"Chyba při hromadné synchronizaci fóra {gid}: {e}")
        finally:
            await r.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--guild_id", type=str, help="ID Discourse fóra pro backfill")
    parser.add_argument("--backfill", action="store_true", help="Spustí jednorázový backfill pro specifikované fórum")
    args = parser.parse_args()

    if args.backfill and args.guild_id:
        async def run_backfill():
            syncer = DiscourseSync()
            await syncer.backfill_guild(args.guild_id)
        asyncio.run(run_backfill())
    else:
        async def main_loop():
            syncer = DiscourseSync()
            print("[DiscourseSync] Služba pro synchronizaci Discourse fór byla spuštěna.")
            while True:
                try:
                    await syncer.sync_all()
                except Exception as e:
                    print(f"[DiscourseSync] Chyba v cyklu synchronizace: {e}")
                await asyncio.sleep(300)

        asyncio.run(main_loop())

