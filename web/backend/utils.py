# Facade for backward compatibility during refactoring

from .core.container import AppContainer
from shared.redis_client import get_redis_client

async def get_activity_stats(*args, **kwargs):
    return await AppContainer.repo.get_activity_stats(*args, **kwargs)


async def get_bot_guilds(*args, **kwargs):
    return await AppContainer.repo.get_bot_guilds(*args, **kwargs)


async def get_cached_roles(*args, **kwargs):
    return await AppContainer.repo.get_cached_roles(*args, **kwargs)


async def get_client(*args, **kwargs):
    return await AppContainer.repo.get_client(*args, **kwargs)


async def get_deep_stats_redis(*args, **kwargs):
    return await AppContainer.repo.get_deep_stats_redis(*args, **kwargs)


async def get_realtime_online_count(*args, **kwargs):
    return await AppContainer.repo.get_realtime_online_count(*args, **kwargs)


async def get_redis_dashboard_stats(*args, **kwargs):
    return await AppContainer.repo.get_redis_dashboard_stats(*args, **kwargs)


async def get_user_guilds(*args, **kwargs):
    return await AppContainer.repo.get_user_guilds(*args, **kwargs)


async def load_member_stats(*args, **kwargs):
    return await AppContainer.repo.load_member_stats(*args, **kwargs)


async def save_user_guilds(*args, **kwargs):
    return await AppContainer.repo.save_user_guilds(*args, **kwargs)


async def get_action_weights(*args, **kwargs):
    return await AppContainer.analytics.get_action_weights(*args, **kwargs)


async def get_engagement_score(*args, **kwargs):
    return await AppContainer.analytics.get_engagement_score(*args, **kwargs)


async def get_health_research_data(*args, **kwargs):
    return await AppContainer.analytics.get_health_research_data(*args, **kwargs)


async def get_insights(*args, **kwargs):
    return await AppContainer.analytics.get_insights(*args, **kwargs)


async def get_security_score(*args, **kwargs):
    return await AppContainer.analytics.get_security_score(*args, **kwargs)


async def get_trend_analysis(*args, **kwargs):
    return await AppContainer.analytics.get_trend_analysis(*args, **kwargs)

import json
import os

from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, Counter
import redis.asyncio as redis
import httpx
import sys
from fastapi import Request, HTTPException

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


from shared.redis_client import get_redis
from shared.config import settings

try:
    from config.dashboard_secrets import BOT_TOKEN
except ImportError:
    BOT_TOKEN = ""

DATA_DIR = Path("data")
CONFIG_PATH = DATA_DIR / "challenge_config.json"



def K_DAU(gid: int, d: str) -> str: 
    return f"hll:dau:{gid}:{d}"



    
    

    


    

async def get_summary_card_data(discord_dau=0, discord_mau=0, discord_wau=0, discord_users=0, guild_id: int = None):
    """
    Get summary card data using ONLY real data from Redis (Primary) and database (Fallback).
    Prioritizes live bot data for user counts.
    """
    r = await get_redis()
    
    real_total_users = discord_users
    real_msgs = 0
    
    try:
        
        total_msgs_str = await r.get(f"stats:total_msgs:{guild_id}")
        real_msgs = int(total_msgs_str) if total_msgs_str else 0
        
        
        bot_total_members = await r.get(f"presence:total:{guild_id}")
        if bot_total_members:
            real_total_users = int(bot_total_members)
            
    except Exception as e:
        print(f"Error fetching Redis stats: {e}")
    finally:
        pass
    
    
    return {
        "discord": {
            "users": real_total_users,
            "msgs": real_msgs,
            "dau": discord_dau,
            "mau": discord_mau,
            "wau": discord_wau
        },
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def get_challenge_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists(): return {}
    try: return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except: return {}

def save_challenge_config(new_config: Dict[str, Any]):
    CONFIG_PATH.write_text(json.dumps(new_config, ensure_ascii=False, indent=2), encoding="utf-8")


    


    
    

    



def generate_security_insights(metrics: Dict[str, Any]):
    """
    Generate a comprehensive list of actionable insights based on calculated metrics.
    Returns structured insights with categories and priority levels.
    Priority: critical (🚨), warning (⚠️), info (ℹ️), success (✅)
    """
    insights = []
    
    
    mod_ratio = metrics.get("mod_ratio", 100)
    users_per_mod = metrics.get("users_per_mod", 100)
    mod_actions = metrics.get("mod_actions", 0)
    ver_level = metrics.get("verification_level", 0)
    mfa_level = metrics.get("mfa_level", 0)
    explicit_filter = metrics.get("explicit_filter", 1)
    participation_rate = metrics.get("participation_rate", 0)
    reply_ratio = metrics.get("reply_ratio", 0)
    voice_hours = metrics.get("voice_hours_per_dau", 0)
    churn_rate = metrics.get("churn_rate", 0)
    stickiness = metrics.get("stickiness", 0)
    overall_score = metrics.get("overall_score", 0)
    total_members = metrics.get("total_members", 0)
    avg_dau = metrics.get("avg_dau", 0)
    growth_rate = metrics.get("growth_rate", 0)
    engagement_score = metrics.get("engagement_score", 50)
    avg_msg_length = metrics.get("avg_msg_length", 0)
    weekend_ratio = metrics.get("weekend_ratio", 1.0)
    new_member_retention = metrics.get("new_member_retention", 100)
    
    def add(priority: str, category: str, title: str, detail: str):
        """Helper to add structured insight"""
        icon_map = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️", "success": "✅", "tip": "💡"}
        icon = icon_map.get(priority, "📊")
        insights.append({
            "priority": priority,
            "category": category,
            "text": f"{icon} **{title}**: {detail}"
        })
    
    
    
    
    
    if mod_ratio < 40:
        add("critical", "team", "Kritický stav", f"{users_per_mod:.0f} členů na moderátora! Urgentně naberte.")
    elif mod_ratio < 60:
        add("warning", "team", "Nedostatek moderátorů", f"{users_per_mod:.0f} uživatelů na mod je nad limitem.")
    elif mod_ratio < 80:
        add("info", "team", "Vytížení týmu", "Poměr je hraniční – mějte záložní členy.")
    elif mod_ratio >= 95 and users_per_mod < 30:
        add("success", "team", "Silný tým", "Skvělý poměr moderátorů – rychlá reakce zaručena.")
    
    if mod_actions == 0:
        add("warning", "team", "Žádná moderace", "Za měsíc 0 akcí. Ověřte logging bota.")
    elif mod_actions < 3:
        add("info", "team", "Klidná komunita", "Minimální zásahy – komunita je ukázněná.")
    elif mod_actions > 100 and mod_actions <= 300:
        add("info", "team", "Aktivní moderace", f"{mod_actions} akcí/měsíc. Tým je bdělý.")
    elif mod_actions > 300 and mod_actions <= 500:
        add("warning", "team", "Vysoká zátěž", f"{mod_actions} akcí. Zvažte rotaci moderátorů.")
    elif mod_actions > 500:
        add("critical", "team", "Přetížení", f"{mod_actions} akcí! Možný systémový problém.")
    
    
    
    
    
    if ver_level == 0:
        add("critical", "security", "Bez ověření", "Kdokoli může psát ihned po vstupu!")
    elif ver_level == 1:
        add("warning", "security", "Slabé ověření", "Pouze e-mail. Zvažte vyšší úroveň.")
    elif ver_level >= 3:
        add("success", "security", "Silné ověření", f"Úroveň {ver_level}/4 – dobrá ochrana.")
    
    if mfa_level == 0:
        add("warning", "security", "Chybí 2FA", "Moderátoři nemají povinné 2FA.")
    else:
        add("success", "security", "2FA aktivní", "Moderátoři mají povinné 2FA.")
    
    if explicit_filter == 0:
        add("warning", "security", "Žádný filtr", "Explicitní obsah není skenován.")
    elif explicit_filter == 1:
        add("info", "security", "Částečný filtr", "Skenování jen u členů bez role.")
    elif explicit_filter == 2:
        add("success", "security", "Plný filtr", "Veškerý obsah je skenován.")
    
    
    
    
    
    if participation_rate < 1:
        add("critical", "activity", "Mrtvý server", "Pod 1% aktivních. Potřeba reaktivace.")
    elif participation_rate < 5:
        add("warning", "activity", "Velmi nízká aktivita", f"Pouze {participation_rate:.1f}% denně aktivních.")
    elif participation_rate < 10:
        add("info", "activity", "Nízké zapojení", f"{participation_rate:.1f}% aktivních. Zkuste eventy.")
    elif participation_rate < 20:
        add("info", "activity", "Průměrná aktivita", f"{participation_rate:.1f}% denní účast.")
    elif participation_rate >= 30:
        add("success", "activity", "Vysoké zapojení", f"{participation_rate:.1f}% aktivních – výborné!")
    
    if reply_ratio < 5:
        add("info", "activity", "Oznámkový styl", "Téměř žádné odpovědi – server je broadcast.")
    elif reply_ratio < 15:
        add("info", "activity", "Málo konverzací", f"{reply_ratio:.0f}% odpovědí. Zkuste ankety.")
    elif reply_ratio >= 40:
        add("success", "activity", "Živá diskuze", f"{reply_ratio:.0f}% zpráv jsou odpovědi!")
    
    if voice_hours < 0.05:
        add("info", "activity", "Prázdné voice", "Téměř nulová hlasová aktivita.")
    elif voice_hours < 0.1:
        add("info", "activity", "Tiché kanály", "Minimální voice. Zkuste events.")
    elif voice_hours >= 0.5:
        add("success", "activity", "Aktivní voice", f"Průměrně {voice_hours:.1f}h/den na uživatele.")
    
    
    
    
    
    if churn_rate > 50:
        add("critical", "retention", "Masový exodus", f"{churn_rate:.0f}% odchodů! Kritické.")
    elif churn_rate > 30:
        add("critical", "retention", "Vysoký odliv", f"{churn_rate:.1f}% opouští. Prověřte příčiny.")
    elif churn_rate > 15:
        add("warning", "retention", "Zvýšený churn", f"{churn_rate:.1f}% odchodů. Zlepšete onboarding.")
    elif churn_rate > 5:
        add("info", "retention", "Normální fluktuace", f"{churn_rate:.1f}% – běžné rozmezí.")
    elif churn_rate <= 2:
        add("success", "retention", "Excelentní retence", "Minimální odchody – členové zůstávají!")
    
    if stickiness < 5:
        add("warning", "retention", "Nízká stickiness", "DAU/MAU pod 5%. Vrací se zřídka.")
    elif stickiness < 15:
        add("info", "retention", "Příležitostní návštěvy", f"Stickiness {stickiness:.0f}% – hobby komunita.")
    elif stickiness < 30:
        add("info", "retention", "Dobrá stickiness", f"{stickiness:.0f}% DAU/MAU – solidní.")
    elif stickiness >= 40:
        add("success", "retention", "Návyková komunita", f"Stickiness {stickiness:.0f}%! Denně se vrací.")
    
    
    
    
    
    if growth_rate < -10:
        add("critical", "growth", "Úbytek členů", f"{growth_rate:.1f}% – server ztrácí lidi.")
    elif growth_rate < 0:
        add("warning", "growth", "Stagnace", f"{growth_rate:.1f}% – mírný pokles.")
    elif growth_rate > 0 and growth_rate < 5:
        add("info", "growth", "Pomalý růst", f"+{growth_rate:.1f}% – stabilní.")
    elif growth_rate >= 5 and growth_rate < 15:
        add("success", "growth", "Zdravý růst", f"+{growth_rate:.1f}% měsíčně.")
    elif growth_rate >= 15:
        add("success", "growth", "Virální růst", f"+{growth_rate:.1f}%! Moderace stíhá?")
    
    
    
    
    
    if avg_msg_length > 0 and avg_msg_length < 20:
        add("info", "community", "Krátké zprávy", f"Průměr {avg_msg_length:.0f} znaků – chat styl.")
    elif avg_msg_length >= 100:
        add("success", "community", "Obsahové diskuze", f"Průměr {avg_msg_length:.0f} znaků – kvalita!")
    
    if weekend_ratio > 1.5:
        add("info", "community", "Víkendová komunita", "1.5x vyšší aktivita o víkendech.")
    elif weekend_ratio < 0.5:
        add("info", "community", "Pracovní komunita", "Aktivnější během týdne.")
    
    if new_member_retention < 30:
        add("warning", "community", "Únik nováčků", "Pod 30% zůstává. Vylepšete onboarding.")
    elif new_member_retention >= 70:
        add("success", "community", "Vítající komunita", f"{new_member_retention:.0f}% nováčků zůstává!")
    
    
    
    
    
    if total_members > 100 and participation_rate < 10 and voice_hours < 0.1:
        add("tip", "tips", "Event tip", "Zkuste voice event nebo AMA session pro oživení.")
    
    if reply_ratio < 20 and participation_rate > 5:
        add("tip", "tips", "Interakce tip", "Přidejte ankety/hlasování pro více konverzací.")
    
    if churn_rate > 10 and new_member_retention < 50:
        add("tip", "tips", "Onboarding tip", "Vytvořte uvítací kanál s pravidly a FAQ.")
    
    if mod_actions > 200 and mod_ratio < 70:
        add("tip", "tips", "Automatizace tip", "Zvažte AutoMod pro odlehčení týmu.")
    
    
    
    
    
    achievements = 0
    if overall_score >= 80: achievements += 1
    if participation_rate >= 20: achievements += 1
    if churn_rate <= 5: achievements += 1
    if mod_ratio >= 90: achievements += 1
    if stickiness >= 30: achievements += 1
    if growth_rate >= 5: achievements += 1
    
    if achievements >= 4:
        add("success", "achievement", "Vzorová komunita", f"Vynikáte v {achievements} oblastech! 🏆")
    elif achievements >= 2:
        add("success", "achievement", "Na dobré cestě", f"Silní ve {achievements} oblastech.")
    
    
    
    
    
    if not insights:
        if overall_score >= 90:
            add("success", "general", "Perfektní kondice", "Všechny metriky jsou ukázkové!")
        elif overall_score >= 70:
            add("success", "general", "Stabilní stav", "Vše v normě. Skvělá práce!")
        else:
            add("info", "general", "Standardní úroveň", "Server funguje – prostor pro růst.")
    
    
    priority_order = {"critical": 0, "warning": 1, "info": 2, "tip": 3, "success": 4}
    insights.sort(key=lambda x: priority_order.get(x["priority"], 5))
    
    
    return [i["text"] for i in insights]






async def get_time_comparisons(guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Calculate WoW and MoM DAU changes relative to end_date."""
    
    if end_date:
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        e_dt = datetime.now()
    
    
    activity_stats = await get_activity_stats(guild_id, end_date=e_dt.strftime("%Y-%m-%d"), days=60)
    dau_data = activity_stats.get("dau_data", [])
    
    
    if len(dau_data) >= 14:
        this_week = sum(dau_data[-7:]) / 7
        last_week = sum(dau_data[-14:-7]) / 7
        wow_change = ((this_week - last_week) / max(1, last_week)) * 100
    else:
        
        this_week = sum(dau_data) / len(dau_data) if dau_data else 0
        last_week = 0
        wow_change = 0 
        
    
    if len(dau_data) >= 60:
        this_month = sum(dau_data[-30:]) / 30
        last_month = sum(dau_data[-60:-30]) / 30
        mom_change = ((this_month - last_month) / max(1, last_month)) * 100
    else:
        
        this_month = sum(dau_data) / len(dau_data) if dau_data else 0
        last_month = 0
        mom_change = 0
        
    return {
        "week_over_week": {
            "this_week": round(this_week, 1),
            "last_week": round(last_week, 1),
            "change_percent": round(wow_change, 1)
        },
        "month_over_month": {
            "this_month": round(this_month, 1),
            "last_month": round(last_month, 1),
            "change_percent": round(mom_change, 1)
        }
    }

async def get_voice_leaderboard(guild_id: int, limit: int = 10, start_date: str = None, end_date: str = None, role_id: str = "all") -> List[Dict[str, Any]]:
    """Fetch top users by voice duration - currently all-time fallback."""
    
    r = await get_redis()
    try:
        data = await r.zrevrange(f"stats:voice_duration:{guild_id}", 0, limit - 1, withscores=True)
        return [{"user_id": uid, "duration_seconds": int(score)} for uid, score in data]
    except Exception as e:
        print(f"Voice stats error: {e}")
        return []

async def get_command_stats(guild_id: int, limit: int = 10, start_date: str = None, end_date: str = None, role_id: str = "all") -> List[Dict[str, Any]]:
    """Fetch top used commands."""
    r = await get_redis()
    try:
        data = await r.hgetall(f"stats:commands:{guild_id}")
        sorted_data = sorted(data.items(), key=lambda item: int(item[1]), reverse=True)[:limit]
        return [{"name": k, "count": int(v)} for k, v in sorted_data]
    except Exception as e:
        print(f"Command stats error: {e}")
        return []

async def get_traffic_stats(guild_id: int, days: int = 30, start_date: str = None, end_date: str = None, role_id: str = "all") -> Dict[str, Any]:
    """Fetch Joins vs Leaves for traffic chart."""
    return await load_member_stats(guild_id, start_date=start_date, end_date=end_date) 

async def get_leaderboard_data(guild_id: int, limit: int = 15, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Fetch user leaderboard with optional date filtering."""
    r = await get_redis()
    try:
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            
            if (end_dt - start_dt).days > 365:
                top_users = await r.zrevrange(f"leaderboard:messages:{guild_id}", 0, limit - 1, withscores=True)
            else:
                
                daily_keys = []
                curr = start_dt
                while curr <= end_dt:
                    daily_keys.append(f"stats:user_daily:{guild_id}:{curr.strftime('%Y%m%d')}")
                    curr += timedelta(days=1)
                
                
                existing_keys = []
                for k in daily_keys:
                    if await r.exists(k): existing_keys.append(k)
                
                if not existing_keys:
                    
                    top_users = await r.zrevrange(f"leaderboard:messages:{guild_id}", 0, limit - 1, withscores=True)
                else:
                    temp_key = f"tmp:leaderboard:{guild_id}:{start_date}:{end_date}"
                    await r.zunionstore(temp_key, existing_keys)
                    await r.expire(temp_key, 60)
                    top_users = await r.zrevrange(temp_key, 0, limit - 1, withscores=True)
        else:
            top_users = await r.zrevrange(f"leaderboard:messages:{guild_id}", 0, limit - 1, withscores=True)

        leaderboard = []
        for user_id_str, msg_count in top_users:
            uid = int(float(user_id_str))
            user_info = await r.hgetall(f"user:info:{uid}") or {}
            name = user_info.get("name", f"User {uid}")
            
            lengths = await r.lrange(f"leaderboard:msg_lengths:{guild_id}:{uid}", 0, -1)
            avg_len = sum(int(l) for l in lengths) / len(lengths) if lengths else 0
            
            leaderboard.append({
                "user_id": uid, "name": name,
                "avatar": user_info.get("avatar"), 
                "total_messages": int(msg_count),
                "avg_message_length": round(avg_len, 1)
            })
        return {"leaderboard": leaderboard}
    except Exception as e:
        print(f"Leaderboard data error: {e}")
        return {"leaderboard": [], "error": str(e)}

async def get_channel_distribution(guild_id: int, start_date: str = None, end_date: str = None, days: int = 30) -> List[Dict[str, Any]]:
    """Fetch message distribution by channel, optionally filtered by date/days."""
    r = await get_redis()
    try:
        
        if not start_date:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days-1)
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = end_dt.strftime("%Y-%m-%d")
            
        if not start_date or not end_date:
            data = await r.zrevrange(f"stats:channel_total:{guild_id}", 0, 14, withscores=True)
            return [{"channel_id": cid, "count": int(score)} for cid, score in data]

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date != datetime.now().strftime("%Y-%m-%d") else datetime.now()
        
        
        if (end_dt - start_dt).days > 365:
            data = await r.zrevrange(f"stats:channel_total:{guild_id}", 0, 14, withscores=True)
            return [{"channel_id": cid, "count": int(score)} for cid, score in data]

        all_channels = await r.zrevrange(f"stats:channel_total:{guild_id}", 0, -1)
        if not all_channels: return []

        pipe = r.pipeline()
        curr, day_count = end_dt, 0
        while curr >= start_dt:
            d_str = curr.strftime("%Y%m%d")
            for cid in all_channels:
                cid_str = cid
                pipe.get(f"stats:channel:{guild_id}:{cid_str}:{d_str}")
            curr -= timedelta(days=1)
            day_count += 1
            if day_count > 365: break 

        responses = await pipe.execute()
        channel_counts = Counter()
        num_channels = len(all_channels)
        
        
        for d_idx in range(day_count):
            for c_idx in range(num_channels):
                val = responses[d_idx * num_channels + c_idx]
                if val is not None:
                    cid_str = all_channels[c_idx] 
                    try:
                        channel_counts[cid_str] += int(float(val))
                    except (ValueError, TypeError):
                        pass
        
        if not channel_counts:
            
            data = await r.zrevrange(f"stats:channel_total:{guild_id}", 0, 14, withscores=True)
            if not data: return [] 
            return [{"channel_id": cid, "count": int(score)} for cid, score in data]
            
        return [{"channel_id": cid, "count": count} for cid, count in channel_counts.most_common(15)]
    except Exception as e:
        print(f"Channel dist error: {e}")
        return []

async def get_dashboard_team(guild_id: int) -> List[Dict[str, Any]]:
    """
    Get all users with explicit dashboard access for a guild.
    """
    r = await get_redis()
    try:
        
        user_ids = await r.smembers(f"dashboard:team:{guild_id}")
        team = []
        
        for uid in user_ids:
            perms = await r.smembers(f"dashboard:perms:{guild_id}:{uid}")
            
            user_info = await r.hgetall(f"user:info:{uid}") or {}
            
            team.append({
                "id": uid,
                "username": user_info.get("username", "Unknown User"),
                "avatar": user_info.get("avatar"),
                "permissions": list(perms)
            })
            
        return team
    except Exception as e:
        print(f"Error fetching dashboard team: {e}")
        return []
    finally:
        pass

async def get_dashboard_permissions(guild_id: int, user_id: str, discord_role: str = "guest") -> List[str]:
    """
    Get effective permissions for a user on a guild.
    """
    
    
    if discord_role == "admin": 
        return ["*"]

    
    from .utils import get_user_guilds
    user_guilds = await get_user_guilds(user_id)
    
    guild_info = next((g for g in user_guilds if str(g["id"]) == str(guild_id)), None)
    
    if not guild_info:
        
        return []

    
    
    
    if guild_info.get("is_admin"):
        return ["*"]

    
    r = await get_redis()
    try:
        perms = await r.smembers(f"dashboard:perms:{guild_id}:{user_id}")
        return list(perms) if perms else []
    except:
        return []

async def add_dashboard_user(guild_id: int, user_id: str, user_data: Dict[str, str], permissions: List[str]):
    """
    Add a user to the dashboard team.
    """
    r = await get_redis()
    try:
        
        await r.sadd(f"dashboard:team:{guild_id}", user_id)
        
        
        perm_key = f"dashboard:perms:{guild_id}:{user_id}"
        await r.delete(perm_key)
        if permissions:
            await r.sadd(perm_key, *permissions)
            
        
        if user_data:
             await r.hset(f"user:info:{user_id}", mapping=user_data)
             
        return True
    except Exception as e:
        print(f"Error adding dashboard user: {e}")
        return False
    finally:
        pass

async def remove_dashboard_user(guild_id: int, user_id: str):
    """
    Remove a user from the dashboard team.
    """
    r = await get_redis()
    try:
        await r.srem(f"dashboard:team:{guild_id}", user_id)
        await r.delete(f"dashboard:perms:{guild_id}:{user_id}")
        return True
    except Exception as e:
        print(f"Error removing dashboard user: {e}")
        return False
    finally:
        pass



async def get_daily_stats(r: redis.Redis, gid: int, uid: int, day: datetime.date) -> dict:
    """
    Get daily stats for a user on a specific day.
    Uses cached value if version matches, otherwise recalculates from raw events.
    """
    from datetime import datetime as dt
    import json
    from collections import defaultdict
    
    day_str = day.strftime("%Y-%m-%d")
    cache_key = f"stats:day:{day_str}:{gid}:{uid}"
    
    
    cached_version = await r.hget(cache_key, "_version")
    current_version = await r.get("config:weights_version") or "0"
    
    if cached_version == current_version:
        
        stats = await r.hgetall(cache_key)
        
        return {k: float(v) if k != "_version" else v for k, v in stats.items()}
    
    
    weights = await get_action_weights(r)
    
    
    from datetime import time as dt_time
    day_start = dt.combine(day, dt_time(0, 0, 0)).timestamp()
    day_end = dt.combine(day, dt_time(23, 59, 59)).timestamp()
    
    stats = defaultdict(float)
    
    
    msg_key = f"events:msg:{gid}:{uid}"
    messages = await r.zrangebyscore(msg_key, day_start, day_end, withscores=True)
    
    last_msg_ts = 0
    raw_chat_time = 0
    SESSION_GAP = 300 
    
    for msg_json, score in messages:
        msg_data = json.loads(msg_json)
        msg_ts = float(score)
        
        
        if last_msg_ts == 0 or (msg_ts - last_msg_ts) > SESSION_GAP:
            raw_chat_time += weights.get("session_base", 180)
        
        last_msg_ts = msg_ts
        
        
        raw_chat_time += msg_data.get("len", 0) * weights.get("char_weight", 1)
        raw_chat_time += weights.get("msg_weight", 0)
        if msg_data.get("reply"):
            raw_chat_time += weights.get("reply_weight", 60)
            
    stats["messages"] += len(messages)
    stats["chat_time"] = raw_chat_time * weights.get("chat_time", 1)
    
    
    voice_key = f"events:voice:{gid}:{uid}"
    voice_sessions = await r.zrangebyscore(voice_key, day_start, day_end)
    
    for vs_json in voice_sessions:
        vs_data = json.loads(vs_json)
        stats["voice_time"] += vs_data["duration"] * weights.get("voice_time", 1)
    
    
    action_key = f"events:action:{gid}:{uid}"
    actions = await r.zrangebyscore(action_key, day_start, day_end)
    
    for action_json in actions:
        action_data = json.loads(action_json)
        action_type = action_data["type"]
        
        
        metric_map = {
            "ban": "bans", "kick": "kicks", "timeout": "timeouts",
            "unban": "unbans", "role_update": "role_updates",
            "msg_delete": "msg_deleted"
        }
        
        metric = metric_map.get(action_type, action_type + "s")
        stats[metric] += 1
    
    
    cache_data = dict(stats)
    cache_data["_version"] = current_version
    await r.hset(cache_key, mapping={k: str(v) for k, v in cache_data.items()})
    
    return dict(stats)

async def update_env_token(token: str):
    """
    Updates the BOT_TOKEN in .env file and in-memory.
    """
    env_path = ROOT / ".env"
    lines = []
    found = False
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("BOT_TOKEN="):
                    lines.append(f"BOT_TOKEN={token}\n")
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f"BOT_TOKEN={token}\n")
        
    with open(env_path, "w") as f:
        f.writelines(lines)
        
    # Update in-memory
    os.environ["BOT_TOKEN"] = token
    
    # Odebráno ukládání do Redis z důvodu bezpečnosti (Token musí být pouze v .env)
    
    return True

async def is_bot_token_set() -> bool:
    """Checks if a valid token is set in env or redis"""
    token = os.getenv("BOT_TOKEN")
    if token and len(token) > 30 and "sem_vloz" not in token:
       return True
    return False


async def get_sidebar_context(request: Request) -> Dict[str, Any]:
    """
    Globally inject sidebar data via Flat Variable Resolution.
    Resolves active guild data server-side and maps to flat template variables.
    """
    user = request.session.get("discord_user")
    guild_id = request.session.get("guild_id")
    
    
    print(f"[Sidebar Debug] Session ID: {guild_id}")
    
    
    if not guild_id:
        q_guild_id = request.query_params.get("guild_id")
        if q_guild_id:
            print(f"[Sidebar Debug] Recovered ID from Query: {q_guild_id}")
            guild_id = q_guild_id
            
            if user:
                request.session["guild_id"] = guild_id
    
    if guild_id == "demo-guild":
        return {
            "sidebar_guild_id": "demo-guild",
            "sidebar_guild_name": "Demo Server",
            "sidebar_guild_icon": "", # Could be a static asset
        }
    
    resolved_guild = None
    
    if user and guild_id:
        
        s_name = request.session.get("guild_name")
        s_icon = request.session.get("guild_icon")
        
        if s_name and s_name not in ["Neznámý server", "Žádný server"]:
            resolved_guild = {"name": s_name, "icon": s_icon}
        
        
        if not resolved_guild:
            try:
                
                from .utils import get_user_guilds
                user_guilds = await get_user_guilds(user["id"])
                
                match = None
                if user_guilds:
                    match = next((g for g in user_guilds if str(g["id"]) == str(guild_id)), None)
                
                
                if not match:
                    r = await get_redis_client()
                    info = await r.hgetall(f"guild:info:{guild_id}")
                    if info and "name" in info:
                        match = {"name": info["name"], "icon": info.get("icon")}
                
                
                if not match:
                     async with httpx.AsyncClient() as client:
                        resp = await client.get(
                            f"https://discord.com/api/v10/guilds/{guild_id}",
                            headers={"Authorization": f"Bot {BOT_TOKEN}"}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            match = {"name": data["name"], "icon": data.get("icon")}
                            
                            r = await get_redis_client()
                            await r.hset(f"guild:info:{guild_id}", mapping={"name": data["name"], "icon": data.get("icon") or ""})
                            
                if match:
                    resolved_guild = match
                    
                    request.session["guild_name"] = resolved_guild["name"]
                    request.session["guild_icon"] = resolved_guild.get("icon")

            except Exception as e:
                print(f"Sidebar Resolution Error: {e}")

    
    
    
    final_name = resolved_guild["name"] if resolved_guild else None
    
    if not final_name and guild_id:
        final_name = "Načítání..." 
        
    final_icon = resolved_guild["icon"] if resolved_guild else None
    
    
    

    return {
        "sidebar_guild_id": guild_id,
        "sidebar_guild_name": final_name,
        "sidebar_guild_icon": final_icon,
        
    }


async def require_auth(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True

async def require_admin(request: Request):
    await require_auth(request)
    if request.session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Prístup pouze pro administrátory")
    return True


from fastapi import Request, HTTPException
from typing import Optional, Union

def get_guild_id(request: Request, guild_id: Optional[str] = None) -> Union[int, str]:
    gid = request.session.get("guild_id")
    if not gid and guild_id:
        gid = guild_id
    
    if not gid:
        raise HTTPException(status_code=400, detail="No guild selected")
        
    if gid == "demo-guild":
        return gid
        
    try:
        return int(gid)
    except (ValueError, TypeError):
        return gid
