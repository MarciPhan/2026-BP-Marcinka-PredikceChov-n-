import asyncio
import httpx
import time
import json
from shared.redis_client import get_redis

class DiscourseSync:
    """
    Konektor pro synchronizaci dat z Discourse fóra do Metricord databáze.
    Tato třída slouží k integraci událostí (témata, příspěvky) z externího fóra.
    """
    
    def __init__(self):
        pass
        
    async def sync_guild(self, guild_id: str):
        """
        Provede synchronizaci fóra se zadaným ID.
        V aktuální verzi stahuje základní statistiky přes Discourse API.
        """
        r = await get_redis()
        try:
            # Načteme konfiguraci z Redis
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
                # Načtení site.json pro základní statistiky
                site_resp = await client.get(f"{url}/site.json", headers=headers)
                if site_resp.status_code != 200:
                    raise Exception(f"Chyba při komunikaci s Discourse API: {site_resp.status_code}")
                    
                # Načtení about.json pro statistiky uživatelů
                about_resp = await client.get(f"{url}/about.json", headers=headers)
                about_data = about_resp.json() if about_resp.status_code == 200 else {}
                
                # Zpracování statistik (simulace Metricord eventů)
                stats = about_data.get("about", {}).get("stats", {})
                
                total_topics = stats.get("topic_count", 0)
                total_posts = stats.get("post_count", 0)
                total_users = stats.get("user_count", 0)
                
                # Uložíme základní statistiky do Redis tak, aby je viděl dashboard
                await r.set(f"presence:total:{guild_id}", total_users)
                await r.set(f"stats:total_msgs:{guild_id}", total_posts)
                
                # Vytvoření falešných DAU pro demonstraci
                now = time.time()
                active_users = stats.get("active_users_7_days", 0)
                estimated_dau = max(1, active_users // 7)
                
                import datetime
                d_str = datetime.datetime.now().strftime("%Y%m%d")
                
                # Pro jednoduchost přidáme náhodná ID do HLL
                for i in range(estimated_dau):
                    await r.pfadd(f"hll:dau:{guild_id}:{d_str}", f"d_user_{i}")
                    
                return True
                
        except Exception as e:
            print(f"Chyba při synchronizaci Discourse (ID: {guild_id}): {e}")
            raise e
        finally:
            await r.close()
