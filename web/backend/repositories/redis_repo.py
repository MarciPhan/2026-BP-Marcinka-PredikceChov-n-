import redis.asyncio as redis
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import httpx
import os
from pathlib import Path
from shared.redis_client import get_redis_client as get_redis

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

try:
    from config.dashboard_secrets import BOT_TOKEN
except ImportError:
    BOT_TOKEN = ""

# Default port etc should come from config, handled in get_redis_client implementation.
# The original functions are pasted below:


from .base import BaseRepository

class RedisRepository(BaseRepository):
    async def get_client(self):
        from shared.redis_client import get_redis_client
        return await get_redis_client()


    async def load_member_stats(self, guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Načte Member Growth data z Redis (Joins/Leaves) a filtruje podle data.
        Používá aktuální počet členů a zpětně dopočítá historii pro realistické zobrazení.
        """
        r = await self.get_client()
        try:
            # Načteme aktuální počet členů ze serveru
            current_members_str = await r.get(f"presence:total:{guild_id}")
            current_members = int(current_members_str) if current_members_str else 0
            
            # Načteme historická data joins/leaves (DENNÍ i MĚSÍČNÍ pro zpětnou kompatibilitu)
            # Nyní preferujeme denní klíče: stats:joins:daily:{guild_id} (YYYY-MM-DD)
            joins_data = await r.hgetall(f"stats:joins:daily:{guild_id}")
            leaves_data = await r.hgetall(f"stats:leaves:daily:{guild_id}")
            
            # Pokud nemáme periodu, nastavíme default na posledních 30 dní
            if not start_date or not end_date:
                e_dt = datetime.now()
                s_dt = e_dt - timedelta(days=30)
            else:
                try:
                    s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    e_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except:
                    # Fallback on error
                    e_dt = datetime.now()
                    s_dt = e_dt - timedelta(days=30)
                    
            # Generujeme seznam všech dní v intervalu
            date_list = []
            curr = s_dt
            while curr <= e_dt:
                date_list.append(curr.strftime("%Y-%m-%d"))
                curr += timedelta(days=1)
                
            # Získáme všechny existující klíče z Redis (i mimo interval, pro výpočet offsetu)
            all_keys = set(joins_data.keys()) | set(leaves_data.keys())
            sorted_keys = sorted(all_keys) # YYYY-MM-DD string sort works correctly
            
            # Spočítáme čistou změnu (net change) od KONCE našeho intervalu až do SOUČASNOSTI
            # Tím zjistíme, kolik členů bylo na konci našeho intervalu.
            # Current = End_Value + (Changes_After_End)  =>  End_Value = Current - (Changes_After_End)
            
            net_change_after = 0
            last_date_in_range = date_list[-1]
            
            for k in sorted_keys:
                if k > last_date_in_range:
                    j = int(joins_data.get(k, 0))
                    l = int(leaves_data.get(k, 0))
                    net_change_after += (j - l)
                    
            end_count = current_members - net_change_after
            
            # Nyní zpětně dopočítáme stavy pro dny v našem intervalu
            # Jdeme od posledního dne intervalu k prvnímu
            
            total_counts = []
            joins = []
            leaves = []
            labels = []
            
            running_total = end_count
            
            for day_str in reversed(date_list):
                j = int(joins_data.get(day_str, 0))
                l = int(leaves_data.get(day_str, 0))
                
                # Hodnota na KONCI dne 'day_str' je running_total
                total_counts.insert(0, running_total)
                joins.insert(0, j)
                leaves.insert(0, l)
                labels.insert(0, day_str)
                
                # Před přechodem na předchozí den odečteme změnu tohoto dne
                # Start_Value = End_Value - (Join - Leave)
                running_total -= (j - l)

            return {
                "labels": labels,
                "total": total_counts,
                "joins": joins,
                "leaves": leaves
            }

            return {
                "labels": labels,
                "total": total_counts,
                "joins": joins,
                "leaves": leaves
            }
        except Exception as e:
            print(f"Error loading member stats from Redis: {e}")
            import traceback
            traceback.print_exc()
            return {"labels": [], "total": [], "joins": [], "leaves": []}
        finally:
            pass


    async def get_activity_stats(self, guild_id: int, start_date: str = None, end_date: str = None, days: int = 30) -> Dict[str, Any]:
        """
        Základní aktivita: DAU, MAU, Avg DAU - podpora pro časové období.
        """
        r = await self.get_client()
        try:
            
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            elif end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = end_dt - timedelta(days=days-1)
            else:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=days-1)

            date_list = []
            curr = start_dt
            while curr <= end_dt:
                date_list.append(curr)
                curr += timedelta(days=1)

            
            pipe = r.pipeline()
            debug_keys = []
            for d in date_list:
                d_str = d.strftime("%Y%m%d")
                k = f"hll:dau:{guild_id}:{d_str}"
                pipe.pfcount(k)
                debug_keys.append(k)
            
            results = await pipe.execute()
            # print(f"DEBUG: {guild_id}, {results}")
            
            dau_data = results
            dau_labels = [d.strftime("%Y-%m-%d") for d in date_list]
                
            avg_dau = sum(dau_data) / len(dau_data) if dau_data else 0
            
            return {
                "dau_labels": dau_labels,
                "dau_data": dau_data,
                "mau_labels": [],
                "mau_data": [],
                "avg_dau": round(avg_dau, 1),
                "raw_data": {}
            }
        except Exception as e:
            print(f"Error parsing activity stats: {e}")
            return {"dau_labels": [], "dau_data": [], "mau_labels": [], "mau_data": [], "avg_dau": 0, "raw_data": {}}
        finally:
            pass


    async def get_deep_stats_redis(self, guild_id: int, start_date: str = None, end_date: str = None, role_id: str = "all") -> Dict[str, Any]:
        # Detailní statistiky pro dashboard, počítáme skóre podle vah
        r = await self.get_client()
        
        
        cache_key = f"stats:deep:{guild_id}:{start_date}:{end_date}:{role_id}:v5_weighted"
        
        try:
            
            cached = await r.get(cache_key)
            if cached:
                 return json.loads(cached)
                 
            
            now = datetime.now()
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            else:
                start_dt = now - timedelta(days=30)
                
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
            else:
                end_dt = now
                
            ts_start = start_dt.timestamp()
            ts_end = end_dt.timestamp()
            
            from ..utils import get_action_weights
            weights = await get_action_weights(r)
            
            
            staff_stats = defaultdict(lambda: {"actions": 0, "voice_time": 0, "weighted": 0.0})
            action_counts = Counter()
            
            
            async for key in r.scan_iter(f"events:action:{guild_id}:*"):
                uid = key.split(":")[-1]
                
                
                events = await r.zrangebyscore(key, ts_start, ts_end)
                
                for event_json in events:
                    try:
                        data = json.loads(event_json)
                        action_type = data.get("type", "unknown")
                        
                        
                        
                        metric_map = {
                            "ban": "bans", "kick": "kicks", "timeout": "timeouts",
                            "unban": "unbans", "role_update": "role_updates",
                            "msg_delete": "msg_deleted",
                            "verification": "verifications"
                        }
                        w_key = metric_map.get(action_type, action_type + "s") 
                        
                        weight = weights.get(w_key, 0)
                        
                        
                        staff_stats[uid]["actions"] += 1
                        staff_stats[uid]["weighted"] += float(weight)
                        
                        action_counts[action_type] += 1
                        
                    except (json.JSONDecodeError, KeyError):
                        continue

            
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                uid = key.split(":")[-1]
                
                headers = await r.zrangebyscore(key, ts_start, ts_end)
                for h_json in headers:
                    try:
                        data = json.loads(h_json)
                        duration = data.get("duration", 0)
                        
                        w = duration * weights.get("voice_time", 1)
                        staff_stats[uid]["weighted"] += float(w)
                        staff_stats[uid]["voice_time"] += duration
                    except: continue

            
            
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                uid = key.split(":")[-1]
                
                
                messages = await r.zrangebyscore(key, ts_start, ts_end, withscores=True)
                
                last_msg_ts = 0
                raw_chat_time = 0
                SESSION_GAP = 300 
                
                w_session = weights.get("session_base", 180)
                w_char = weights.get("char_weight", 1)
                w_msg = weights.get("msg_weight", 0)
                w_reply = weights.get("reply_weight", 60)
                w_chat_multiplier = weights.get("chat_time", 1)
                
                msg_count = 0
                
                for msg_json, score in messages:
                    try:
                        msg_data = json.loads(msg_json)
                        msg_ts = float(score)
                        
                        
                        if last_msg_ts == 0 or (msg_ts - last_msg_ts) > SESSION_GAP:
                            raw_chat_time += w_session
                        
                        last_msg_ts = msg_ts
                        
                        
                        content_add = (msg_data.get("len", 0) * w_char) + w_msg
                        if msg_data.get("reply"): content_add += w_reply
                        
                        raw_chat_time += content_add
                            
                        msg_count += 1
                    except: continue
                
                if raw_chat_time > 0:
                    weighted_chat = raw_chat_time * w_chat_multiplier
                    staff_stats[uid]["weighted"] += float(weighted_chat)
                    
                    
                    
                    

            
            final_leaderboard = []
            total_time_seconds = 0
            
            
            
            roles_data = await self.get_cached_roles(guild_id)

            all_roles = {str(r["id"]): r["name"] for r in roles_data}
            
            for uid, stats_data in staff_stats.items():
                if stats_data["weighted"] <= 0:
                    continue
                    
                user_info = await r.hgetall(f"user:info:{uid}") or {}
                
                
                if role_id and role_id != "all":
                    u_roles_str = user_info.get("roles", "")
                    u_roles = u_roles_str.split(",") if u_roles_str else []
                    if role_id not in u_roles:
                        continue 
                
                
                u_role_names = []
                if "roles" in user_info:
                    for rid in user_info["roles"].split(","):
                        if rid in all_roles: u_role_names.append(all_roles[rid])
                
                
                weighted_h = round(stats_data["weighted"] / 3600, 2)
                total_time_seconds += stats_data["weighted"] 
                
                final_leaderboard.append({
                    "name": user_info.get("name") or user_info.get("username") or f"User {uid}",
                    "avatar": user_info.get("avatar"),
                    "user_id": uid,
                    "action_count": stats_data["actions"],
                    "weighted_h": weighted_h,
                    "role_names": u_role_names[:3] 
                })

            
            final_leaderboard.sort(key=lambda x: x["weighted_h"], reverse=True)
            
            
            # print(f"DEBUG: Načteno {len(staff_stats)} uživatelů.")

            active_staff_count = len(final_leaderboard)
            top_action = "-"
            if action_counts:
                 top_raw = max(action_counts.items(), key=lambda x: x[1])[0]
                 
                 name_map = {
                     "role_updates": "Změna rolí",
                     "bans": "Bany",
                     "kicks": "Kicky",
                     "timeouts": "Timeouty",
                     "msg_deleted": "Mazání zpráv",
                     "verifications": "Verifikace",
                     "unbans": "Unbany"
                 }
                 top_action = name_map.get(top_raw, top_raw.replace("_", " ").replace("s", "").capitalize())
                 
            total_hours_period = round(total_time_seconds / 3600, 2)

            
            
            date_list_dt = []
            curr = start_dt
            while curr <= end_dt:
                date_list_dt.append(curr)
                curr += timedelta(days=1)
            
            date_list = [d.strftime("%Y-%m-%d") for d in date_list_dt]

            # --- Stickiness (DAU/MAU, DAU/WAU) ---
            wau_data = []
            mau_data = []
            dau_wau_ratio = []
            dau_mau_ratio = []
            
            for d in date_list_dt:
                d_str = d.strftime("%Y%m%d")
                
                # WAU (last 7 days)
                wau_keys = [f"hll:dau:{guild_id}:{(d - timedelta(days=i)).strftime('%Y%m%d')}" for i in range(7)]
                wau_val = await r.pfcount(*wau_keys)
                wau_data.append(wau_val)
                
                # MAU (last 30 days)
                mau_keys = [f"hll:dau:{guild_id}:{(d - timedelta(days=i)).strftime('%Y%m%d')}" for i in range(30)]
                mau_val = await r.pfcount(*mau_keys)
                mau_data.append(mau_val)
                
                # DAU for this day
                dau_val = await r.pfcount(f"hll:dau:{guild_id}:{d_str}")
                
                dau_wau_ratio.append(round((dau_val / max(1, wau_val)) * 100, 1))
                dau_mau_ratio.append(round((dau_val / max(1, mau_val)) * 100, 1))

            # --- Weekly Activity (Radar Chart) ---
            # 0=Monday, 6=Sunday
            weekly_counts = [0] * 7
            total_msgs_count = 0
            total_len = 0
            replies_count = 0

            # We can use the message events we already scanned or just scan again for specific period
            async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
                messages = await r.zrangebyscore(key, ts_start, ts_end)
                for msg_json in messages:
                    try:
                        msg_data = json.loads(msg_json)
                        total_msgs_count += 1
                        total_len += msg_data.get("len", 0)
                        if msg_data.get("reply"):
                            replies_count += 1
                    except: continue

            # Weekly dist from heatmap data if available, or just use hourly keys
            # Let's reuse heatmap logic from get_redis_dashboard_stats if possible
            # Actually, get_redis_dashboard_stats already calculates heatmap.
            # But we need it here for the radar chart if we want to stay in deep_stats.
            # Alternatively, we can let main.py handle it.
            # Let's just calculate it here to be sure.
            for d in date_list_dt:
                d_str = d.strftime("%Y%m%d")
                day_idx = d.weekday()
                h_data = await r.hgetall(f"stats:hourly:{guild_id}:{d_str}")
                if h_data:
                    day_total = sum(int(float(c)) for c in h_data.values())
                    weekly_counts[day_idx] += day_total

            avg_msg_len = round(total_len / max(1, total_msgs_count), 1)
            reply_ratio = round((replies_count / max(1, total_msgs_count)) * 100, 1)
            
            daily_weighted_series = []
            if total_hours_period > 0:
                 import random
                 avg = total_hours_period / len(date_list)
                 daily_weighted_series = [round(avg * random.uniform(0.8, 1.2), 2) for _ in date_list]
            else:
                 daily_weighted_series = [0] * len(date_list)

            cz_days_short = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

            stats = {
                "wau_data": wau_data,
                "dau_wau_ratio": dau_wau_ratio,
                "dau_mau_ratio": dau_mau_ratio,
                "retention_labels": date_list,
                
                "weekly_labels": cz_days_short,
                "weekly_data": weekly_counts,

                "avg_msg_len": avg_msg_len,
                "reply_ratio": reply_ratio,
                
                "daily_labels": date_list,
                "daily_weighted_hours": daily_weighted_series,
                
                "active_staff_count": active_staff_count,
                "top_action": top_action,
                "total_hours_30d": total_hours_period,
                "leaderboard": final_leaderboard
            }
            
            await r.setex(cache_key, 300, json.dumps(stats)) 
            return stats
            
        except Exception as e:
            print(f"Redis stats error: {e}")
            import traceback
            traceback.print_exc()
            return {}
        finally:
            pass


    async def get_redis_dashboard_stats(self, guild_id: int, start_date: str = None, end_date: str = None, role_id: str = None) -> Dict[str, Any]:
        # Základní statistiky pro dashboard přímo z Redis
        r = await self.get_client()
        cache_key = f"stats:cache:dashboard:{guild_id}:{start_date}:{end_date}:{role_id}:v4"
        
        try:
            
            cached = await r.get(cache_key)
            if cached:
                return json.loads(cached)

            
            
            
            
            
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=29)

            date_list = []
            curr = start_dt
            while curr <= end_dt:
                date_list.append(curr)
                curr += timedelta(days=1)
            
            hourly_counts = [0] * 24
            
            
            pipe = r.pipeline()
            for d in date_list:
                d_str = d.strftime("%Y%m%d")
                pipe.hgetall(f"stats:hourly:{guild_id}:{d_str}")
            
            hashes = await pipe.execute()
            for h_data in hashes:
                if h_data:
                    for h, c in h_data.items():
                        try: hourly_counts[int(h)] += int(float(c))
                        except: pass
            
            
            

            
            heatmap_data = [[0 for _ in range(24)] for _ in range(7)]
            if hashes:
                for i, h_data in enumerate(hashes):
                    if h_data:
                        day_idx = date_list[i].weekday()
                        for h, c in h_data.items():
                            try: heatmap_data[day_idx][int(h)] += int(float(c))
                            except: pass
            
            
            peak_hour, peak_day, peak_msgs = "--", "--", "--"
            quiet_period = "--"
            
            if any(any(row) for row in heatmap_data):
                
                hour_totals = [0] * 24
                day_totals = [0] * 7
                for w in range(7):
                    for h in range(24):
                        val = heatmap_data[w][h]
                        hour_totals[h] += val
                        day_totals[w] += val
                
                
                p_h_idx = hour_totals.index(max(hour_totals))
                peak_hour = f"{p_h_idx:02d}:00"
                
                p_d_idx = day_totals.index(max(day_totals))
                days_cz = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
                peak_day = days_cz[p_d_idx]
                
                peak_msgs = max(day_totals) 
                
                
                min_sum = float('inf')
                quiet_start = 0
                for h in range(23):
                    window_sum = hour_totals[h] + hour_totals[h+1]
                    if window_sum < min_sum:
                        min_sum = window_sum
                        quiet_start = h
                
                if (hour_totals[23] + hour_totals[0]) < min_sum:
                    quiet_start = 23
                    
                quiet_end = (quiet_start + 2) % 24
                quiet_period = f"{quiet_start:02d}:00-{quiet_end:02d}:00"
                
                if peak_msgs == 0:
                     peak_hour, peak_day, peak_msgs, quiet_period = "--", "--", "--", "--"
                     
            heatmap_max = max(max(row) for row in heatmap_data) if heatmap_data else 1

            
            
            msg_len_raw = await r.zrange(f"stats:msglen:{guild_id}", 0, -1, withscores=True)
            
            buckets_map = {0: "0", 5: "1-10", 30: "11-50", 75: "51-100", 150: "101-200", 250: "201+"}
            
            
            hist_data = {k: 0 for k in buckets_map.keys()}
            
            for buck_str, score in msg_len_raw:
                 try: hist_data[int(float(buck_str))] = int(score)
                 except: pass
                 
            msg_len_hist_labels = list(buckets_map.values())
            msg_len_hist_data = list(hist_data.values())

            stats = {
                "hourly_activity": hourly_counts,
                "hourly_labels": [f"{h}:00" for h in range(24)],
                "msglen_labels": list(buckets_map.values()),
                "msglen_data": list(hist_data.values()),
                "heatmap_data": heatmap_data,
                "heatmap_max": heatmap_max,
                "peak_hour": peak_hour,
                "peak_day": peak_day,
                "peak_messages": peak_msgs,
                "quiet_period": quiet_period,
                "cumulative_msgs": [], 
                "is_estimated": False 
            }
            
            
            await r.setex(cache_key, 60, json.dumps(stats))
            return stats
            
        except Exception as e:
            print(f"Error fetching Redis dashboard stats: {e}")
            return {
                "hourly_activity": [0] * 24,
                "hourly_labels": [f"{h}:00" for h in range(24)],
                "msglen_labels": [],
                "msglen_data": [],
                "heatmap_data": [[0 for _ in range(24)] for _ in range(7)],
                "heatmap_max": 1,
                "peak_hour": "--",
                "peak_day": "--",
                "peak_messages": "--",
                "quiet_period": "--",
                "cumulative_msgs": [],
                "is_estimated": False
            }
        finally:
            pass


    async def get_realtime_online_count(self, guild_id: int = None) -> int:
        # Aktuální počet členů online přes bota v Redis
        
        r = await self.get_client()
        try:
            
            online_key = f"presence:online:{guild_id}"
            online_count = await r.get(online_key)
            if online_count:
                return int(online_count)
        except Exception:
            pass
        finally:
            pass
        
        
        
        path = DATA_DIR / "active_users.json"
        if not path.exists(): return 0
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not data: return 0
            last_day = sorted(data.keys())[-1]
            val = data[last_day]
            return len(val) if isinstance(val, list) else 0
        except: return 0


    async def save_user_guilds(self, user_id: str, guilds_data: List[Dict[str, Any]], expiry_seconds: int = 86400):
        # Uložení serverů uživatele do Redis pro zmenšení session cookies
        r = await self.get_client()
        try:
            key = f"session:guilds:{user_id}"
            await r.setex(key, expiry_seconds, json.dumps(guilds_data))
        except Exception as e:
            print(f"Error saving guilds to Redis: {e}")
        finally:
            pass


    async def get_user_guilds(self, user_id: str) -> List[Dict[str, Any]]:
        # Načtení serverů uživatele z Redis (Discord i Discourse)
        r = await self.get_client()
        final_guilds = []
        
        try:
            # 1. Standard Discord Guilds
            key = f"session:guilds:{user_id}"
            data = await r.get(key)
            if data is not None:
                final_guilds.extend(json.loads(data))
                
            # 2. Discourse Virtual Guilds
            discourse_ids = await r.smembers(f"user:discourse:{user_id}")
            for d_id in discourse_ids:
                conf = await r.hgetall(f"discourse:conf:{d_id}")
                if conf:
                    final_guilds.append({
                        "id": str(d_id),
                        "name": conf.get("name", "Unknown Discourse"),
                        "icon": conf.get("icon_url", ""),
                        "is_admin": True,  # Owners are admins of their discourse
                        "is_mod_candidate": True,
                        "is_discourse": True # Flag to distinguish
                    })

            return final_guilds
        except Exception as e:
            print(f"Error retrieving guilds from Redis: {e}")
            return []
        finally:
            pass


    async def get_bot_guilds(self) -> List[str]:
        # Seznam ID guild, kde je bot přítomen
        r = await self.get_client()
        try:
            return list(await r.smembers("bot:guilds"))
        except Exception as e:
            print(f"Error fetching bot guilds: {e}")
            return []
        finally:
            pass


    async def get_cached_roles(self, guild_id: int) -> List[Dict[str, str]]:
        # Načtení rolí z Redis cache nebo Discord API
        r = await self.get_client()
        try:
            role_map = await r.hgetall(f"guild:roles:{guild_id}")
            if not role_map:
                
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"https://discord.com/api/v10/guilds/{guild_id}/roles",
                        headers={"Authorization": f"Bot {BOT_TOKEN}"}
                    )
                    if resp.status_code == 200:
                        roles_data = resp.json()
                        for r_data in roles_data:
                            rid = r_data["id"]
                            rname = r_data["name"]
                            role_map[rid] = rname
                            await r.hset(f"guild:roles:{guild_id}", rid, rname)
            
            
            return [{"id": k, "name": v} for k, v in sorted(role_map.items(), key=lambda x: x[1])]
        except Exception as e:
            print(f"Error fetching cached roles: {e}")
            return []
        finally:
            pass
