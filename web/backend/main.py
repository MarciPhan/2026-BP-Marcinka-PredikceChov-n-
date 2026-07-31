# Backend pro CommunityMetrics Dashboard

from fastapi import FastAPI, Request, Form, Cookie, Response, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
import os

# Načtení environment proměnných z .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key] = val.strip('"').strip("'")

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import urllib.parse
from pathlib import Path
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import secrets
import httpx
import sys
from pathlib import Path

# Add root to sys.path to allow importing scripts
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from scripts.discourse_sync import DiscourseSync
except ImportError:
    DiscourseSync = None

from shared.redis_client import get_redis_client

# Načtení tajných klíčů
try:
    from config.dashboard_secrets import (
        SECRET_KEY, ACCESS_TOKEN, SESSION_EXPIRY_HOURS,
        DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI,
        ADMIN_USER_IDS, BOT_TOKEN
    )
except ImportError:
    # fallback to generated secrets for dev
    SECRET_KEY = secrets.token_urlsafe(32)
    ACCESS_TOKEN = secrets.token_urlsafe(32)
    SESSION_EXPIRY_HOURS = 24
    DISCORD_CLIENT_ID = ""
    DISCORD_CLIENT_SECRET = ""
    DISCORD_REDIRECT_URI = "http://localhost:8093/auth/callback"
    ADMIN_USER_IDS = []
    BOT_TOKEN = ""
    print("VAROVÁNÍ: Používají se generované klíče (dev mode).")




from .utils import (
    load_member_stats, 
    get_activity_stats, 
    get_deep_stats_redis,
    get_challenge_config, 
    save_challenge_config,
    get_realtime_online_count,
    get_summary_card_data,
    get_redis_dashboard_stats,
    save_user_guilds,
    get_user_guilds,
    get_bot_guilds,
    get_trend_analysis, get_engagement_score, get_insights, get_security_score,
    get_voice_leaderboard, get_command_stats, get_traffic_stats, get_channel_distribution,
    get_time_comparisons, get_leaderboard_data,
    get_dashboard_team, add_dashboard_user, remove_dashboard_user, get_dashboard_permissions,
    get_daily_stats, get_action_weights,
    is_bot_token_set, update_env_token, get_health_research_data
)


try:
    from .demo_data import get_demo_stats
except ImportError:
    get_demo_stats = lambda *args: {}

from .otp_utils import (
    validate_email, get_user_role, generate_otp, store_otp, verify_otp, 
    check_rate_limit, send_otp_email, mask_email
)

app = FastAPI(title="CommunityMetrics", docs_url=None, redoc_url=None, openapi_url=None)
# Vypneme automatickou dokumentaci pro čistotu


app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=SESSION_EXPIRY_HOURS * 3600, same_site="lax", https_only=True)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"REQUEST: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# Import a registrace nově oddělených routerů (MVC architektura)
from .routers.auth import router as auth_router
from .routers.settings import router as settings_router
from .routers.pages import router as pages_router
from .routers.api import router as api_router

app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(pages_router)
app.include_router(api_router)







@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/img/favicon.png") 




















async def _dashboard_logic(request: Request, start_date: str = None, end_date: str = None, role_id: str = None):
    # Hlavní logika dashboardu
    
    user = request.session.get("discord_user")
    
    
    if not user:
        
        
        
        
        try:
             r = await get_redis_client()
             bot_guilds = await r.smembers("bot:guilds")
             
             
             total_msgs = 0
             total_users = 0
             max_days = 0
             
             for gid in bot_guilds:
                 if not str(gid).isdigit():
                     continue
                 tm = await r.get(f"stats:total_msgs:{gid}") or "0"
                 tu = await r.get(f"presence:total:{gid}") or "0"
                 hourly = await r.keys(f"stats:hourly:{gid}:*")
                 
                 total_msgs += int(tm)
                 total_users += int(tu)
                 max_days = max(max_days, len(hourly))
             
             pass
             
             # MARKETING STATS (Impressive defaults for the demo)
             # We use the real counts as offsets if they exist, but ensure a high minimum
             display_msgs = max(total_msgs, 1250000)
             display_users = max(total_users, 15340)
             
             public_stats = {
                 "messages": f"{display_msgs:,}".replace(",", " ") + "+",
                 "users": f"{display_users:,}".replace(",", " ") + "+",
                 "days": max(max_days, 365)
             }
        except Exception as e:
            print(f"Error fetching dashboard guilds: {e}")
            public_stats = {"messages": "---", "users": "---", "days": "0"}
             
        return templates.TemplateResponse("landing.html", {"request": request, "stats": public_stats})

    # Restrict guest users
    if request.session.get("role") == "guest" and request.session.get("guild_id") != "demo-guild":
        return RedirectResponse(url="/leaderboard")
    
    guild_id = request.session.get("guild_id")
    if not guild_id:
        return RedirectResponse(url="/select-server")

    if guild_id == "demo-guild":
        # SERVE MOCK DATA
        stats = get_demo_stats(start_date, end_date)
        context = {
            "request": request,
            **stats, # unpacking all the pre-calculated stats
            "user": user,
            "is_demo": True,
            "is_discourse": False
        }
        sidebar_ctx = await get_sidebar_context(request)
        context.update(sidebar_ctx)
        return templates.TemplateResponse("index.html", context)
    
    
    start_date = start_date or request.session.get("start_date", "2025-12-21")
    end_date = end_date or request.session.get("end_date", "2026-01-20")
    role_id = role_id or request.session.get("role_id", "all")
    
    
    request.session["start_date"] = start_date
    request.session["end_date"] = end_date
    request.session["role_id"] = role_id

    guild_id = int(guild_id)
    
    # Check if this is a Discourse guild for context
    is_discourse = False
    if guild_id < 0: # Our negative ID convention for Discourse
        is_discourse = True
    
    
    from .utils import get_dashboard_permissions
    perms = await get_dashboard_permissions(guild_id, user["id"])
    
    
    if not perms:
        try:
             
             r = await get_redis_client()
             xp_key = f"levels:xp:{guild_id}"
             top_users = await r.zrevrange(xp_key, 0, 49, withscores=True) 
             
             leaderboard_data = []
             for i, (uid_str, xp_score) in enumerate(top_users, 1):
                 uid = str(uid_str)
                 xp = int(float(xp_score))
                 
                 u_info = await r.hgetall(f"user:info:{uid}") or {}
                 username = u_info.get("username") or u_info.get("name") or f"Uživatel {uid[:5]}..."
                 avatar = u_info.get("avatar")
                 
                 # Výpočet levelu na základě XP
                 
                 xp_conf = await r.hgetall("config:xp_formula")
                 a = int(xp_conf.get("a", 50))
                 b = int(xp_conf.get("b", 200)) 
                 c_const = int(xp_conf.get("c", 100))
                 
                 import math
                 def calc_level(cxp):
                     if cxp < c_const: return 0
                     c_val = c_const - cxp
                     d = (b**2) - (4*a*c_val)
                     if d < 0: return 0
                     return int((-b + math.sqrt(d)) / (2*a))
                 
                 def xp_for_lvl(lvl):
                     return a * (lvl ** 2) + b * lvl + c_const
                     
                 level = calc_level(xp)
                 next_xp = xp_for_lvl(level + 1)
                 prev_xp = xp_for_lvl(level) if level > 0 else 0
                 
                 needed = next_xp - prev_xp
                 current = xp - prev_xp
                 progress = int((current / needed) * 100) if needed > 0 else 0
                 
                 leaderboard_data.append({
                     "rank": i,
                     "username": username,
                     "user_id": uid,
                     "avatar": avatar,
                     "level": level,
                     "xp": xp,
                     "progress": min(100, max(0, progress))
                 })
                 
             return templates.TemplateResponse("leaderboard.html", {
                 "request": request, 
                 "leaderboard": leaderboard_data, 
                 "user": user,
                 "is_restricted": True
             })
             
        except Exception as e:
            print(f"Restricted view error: {e}")
            return templates.TemplateResponse("leaderboard.html", {"request": request, "leaderboard": [], "user": user, "error": str(e)})

    
    
    
    from .utils import get_cached_roles
    roles = await get_cached_roles(guild_id)
    roles_list = [(r["id"], r["name"]) for r in roles]


    



    
    member_stats = await load_member_stats(guild_id, start_date=start_date, end_date=end_date)
    
    
    activity_stats = await get_activity_stats(guild_id, start_date=start_date, end_date=end_date)
    
    
    deep_stats = await get_deep_stats_redis(guild_id=guild_id, start_date=start_date, end_date=end_date)
    
    
    redis_stats = await get_redis_dashboard_stats(guild_id, start_date=start_date, end_date=end_date, role_id=role_id)
    deep_stats.update(redis_stats)
    
    
    realtime_active = await get_realtime_online_count(guild_id)



    
    summary = await get_summary_card_data(guild_id=guild_id)
    has_any_data = summary["discord"]["msgs"] > 0

    
    total_leaves = sum(member_stats["leaves"]) if member_stats.get("leaves") else 0
    current_total = member_stats["total"][-1] if member_stats.get("total") else 0
    current_dau = activity_stats["dau_data"][-1] if activity_stats.get("dau_data") else 0
    current_mau = activity_stats["mau_data"][-1] if activity_stats.get("mau_data") else 0
    current_wau = deep_stats.get("wau_data", [])[-1] if deep_stats.get("wau_data") else 0
    
    
    summary_stats = await get_summary_card_data(
        discord_dau=current_dau,
        discord_mau=current_mau,
        discord_wau=current_wau,
        discord_users=current_total, 
        guild_id=guild_id
    )
    
    
    real_total_members = summary_stats["discord"]["users"]
    churn_rate = round((total_leaves / max(1, real_total_members)) * 100, 2)
    
    
    context = {
        "request": request,
        "stats": summary_stats,
        "member_stats": member_stats,
        "activity_stats": activity_stats,
        "deep_stats": deep_stats,
        "redis_stats": redis_stats,
        "realtime_active": realtime_active,
        "churn_rate": churn_rate,
        "active_staff_count": 0, 
        "roles": roles_list,
        "user_role": role_id,
        "start_date": start_date,
        "end_date": end_date,
        "guild_id": guild_id,
        "is_discourse": is_discourse,
        "user": user,
        
        
        "total_members": summary_stats["discord"]["users"],
        "avg_dau": activity_stats.get("avg_dau", 0),
        "avg_msg_len": deep_stats.get("avg_msg_len", "-"),
        "peak_day": deep_stats.get("peak_day", "-"),
        "reply_ratio": deep_stats.get("reply_ratio", 0),
        
        
        "dau_labels": activity_stats.get("dau_labels", []),
        "dau_data": activity_stats.get("dau_data", []),
        "labels": member_stats.get("labels", []),
        "joins_data": member_stats.get("joins", []),
        "leaves_data": member_stats.get("leaves", []),
        "total_data": member_stats.get("total", []),
        
        
        "hourly_labels": redis_stats.get("hourly_labels", []),
        "hourly_activity": redis_stats.get("hourly_activity", []),
        "retention_labels": deep_stats.get("retention_labels", []),
        "dau_mau_ratio": deep_stats.get("dau_mau_ratio", []),
        "dau_wau_ratio": deep_stats.get("dau_wau_ratio", []),
        "msglen_labels": redis_stats.get("msglen_labels", []),
        "msglen_data": redis_stats.get("msglen_data", []),
        "weekly_labels": deep_stats.get("weekly_labels", []),
        "weekly_data": deep_stats.get("weekly_data", []),
        "widget_order": request.session.get("overview_order", [])
    }

    
    sidebar_ctx = await get_sidebar_context(request)
    context.update(sidebar_ctx)
    
    return templates.TemplateResponse("index.html", context)




async def require_auth(request: Request):
    # Kontrola, jestli je uživatel přihlášen
    
    allowed_paths = ["/login", "/auth/callback", "/logout", "/login-email", "/api/auth/request-otp", "/verify-otp", "/api/auth/verify-otp", "/resend-otp"]
    if request.url.path.startswith("/static") or request.url.path in allowed_paths:
        return
    
    
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    
    login_time = request.session.get("login_time")
    if login_time:
        elapsed = (datetime.now() - datetime.fromisoformat(login_time)).total_seconds()
        if elapsed > (SESSION_EXPIRY_HOURS * 3600):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Session expired")

async def require_admin(request: Request):
    # Kontrola admin práv
    await require_auth(request)
    if request.session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Přístup pouze pro administrátory")


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR.parent / "frontend" / "templates"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"

@app.get("/docs/{path:path}")
async def docs_proxy(request: Request, path: str = ""):
    # V dev režimu přesměrujeme na VitePress dev server (port 5173)
    # V produkci by zde bylo mountování statických souborů z docs-site/.vitepress/dist
    VITE_DOCS_URL = os.getenv("VITE_DOCS_URL", "http://localhost:5173")
    
    # Pokud cesta nekončí lomítkem ani nemá příponu, přidáme .html pro Vite kompatibilitu (interně)
    # Ale VitePress dev server obvykle zvládá čisté URL.
    target_url = f"{VITE_DOCS_URL}/{path}"
    return RedirectResponse(url=target_url)


@app.exception_handler(401)
async def redirect_to_login_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/", status_code=302)























    
    
    









    

























if __name__ == "__main__":
    uvicorn.run("dashboard.main:app", host="0.0.0.0", port=8092, reload=True)



from typing import Union
def get_guild_id(request: Request, guild_id: Optional[str] = None) -> Union[int, str]:
    """Helper to get guild ID from session or param."""
    gid = request.session.get("guild_id")
    if not gid and guild_id:
        gid = guild_id
    
    print(f"[DEBUG] get_guild_id: session={request.session.get('guild_id')}, param={guild_id} -> Result={gid}")
    
    if not gid:
        raise HTTPException(status_code=400, detail="No guild selected")
        
    if gid == "demo-guild":
        return gid
        
    try:
        return int(gid)
    except (ValueError, TypeError):
        return gid


async def get_discord_channels(guild_id: Any):
    if guild_id == "demo-guild":
        return [
            {"id": "1", "name": "obecné"},
            {"id": "2", "name": "hry"},
            {"id": "3", "name": "pokec"}
        ]
    """Fetch channels from Discord API."""
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"Bot {BOT_TOKEN}"})
        if resp.status_code == 200:
            return resp.json()
    return []







