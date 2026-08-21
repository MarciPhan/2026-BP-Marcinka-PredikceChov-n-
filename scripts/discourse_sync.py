import asyncio
import httpx
import time
import json
from shared.redis_client import get_redis

class DiscourseSync:
    """
    Konektor pro synchronizaci dat z Discourse fóra do CommunityMetrics databáze.
    Tato třída slouží k integraci událostí (témata, příspěvky) z externího fóra.
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        
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
                # Načtení topics (latest)
                topics_resp = await client.get(f"{url}/latest.json", headers=headers)
                if topics_resp.status_code != 200:
                    raise Exception(f"Chyba při komunikaci s Discourse API: {topics_resp.status_code}")
                    
                topics_data = topics_resp.json()
                topics = topics_data.get("topic_list", {}).get("topics", [])
                
                # Zpracování témat idempotně
                synced_set_key = f"discourse:synced_topics:{guild_id}"
                new_msgs = 0
                
                for topic in topics:
                    t_id = str(topic.get("id"))
                    
                    # Idempotence: Zkontrolujeme, zda už jsme toto téma zpracovali
                    is_member = await r.sismember(synced_set_key, t_id)
                    if is_member:
                        continue
                        
                    # Přidáme do setu zpracovaných
                    await r.sadd(synced_set_key, t_id)
                    
                    # Vytvoření eventu
                    import datetime
                    created_at_str = topic.get("created_at")
                    try:
                        dt = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        ts = dt.timestamp()
                    except:
                        ts = time.time()
                        
                    event_data = {
                        "id": t_id,
                        "title": topic.get("title"),
                        "source": "discourse",
                        "reaction_count": topic.get("like_count", 0)
                    }
                    
                    await r.zadd(f"events:msg:{guild_id}:discourse", {json.dumps(event_data): ts})
                    new_msgs += 1
                    
                if new_msgs > 0:
                    await r.incrby(f"stats:total_msgs:{guild_id}", new_msgs)
                    
                return True
                
        except Exception as e:
            print(f"Chyba při synchronizaci Discourse (ID: {guild_id}): {e}")
            raise e
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

