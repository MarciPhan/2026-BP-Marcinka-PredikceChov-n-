from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import secrets

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="web/frontend/templates")

def require_auth(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True

# ... missing imports (get_sidebar_context etc will be added later or imported from utils)
from ..utils import *
import os
from ..demo_data import get_demo_stats, get_demo_user_activity
from collections import defaultdict
from datetime import datetime, timedelta

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")

@router.get("/select-server", response_class=HTMLResponse)
async def select_server_page(request: Request):
    # Výběr serveru pro správu
    user = request.session.get("discord_user")
    if not user:
        return RedirectResponse(url="/")
        
    
    user_guilds = await get_user_guilds(user["id"])
    
    # Restrict guest users (but not demo)
    if request.session.get("role") == "guest":
        return RedirectResponse(url="/leaderboard")
    
    
    if user_guilds is None:
        return RedirectResponse(url="/login")
        
    bot_guilds = await get_bot_guilds()
    
    
    for g in user_guilds:
        # Check if bot is in guild OR if it is a virtual Discourse guild
        g["bot_in_guild"] = (str(g["id"]) in bot_guilds) or g.get("is_discourse", False)
        
    token_required = not (await is_bot_token_set())
    is_admin = request.session.get("role") == "admin"
        
    # Generování CSRF tokenu, pokud není v session
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("select_server.html", {
        "request": request, 
        "guilds": user_guilds,
        "user": user,
        "client_id": DISCORD_CLIENT_ID,
        "token_required": token_required,
        "is_admin": is_admin,
        "csrf_token": request.session["csrf_token"]
    })


@router.get("/select-server/{guild_id}")
async def set_active_server(request: Request, guild_id: str):
    # Nastavení aktivního serveru v session
    user = request.session.get("discord_user")
    if not user:
        return RedirectResponse(url="/")

    
    user_guilds = await get_user_guilds(user["id"])
    if not any(str(g["id"]) == str(guild_id) for g in user_guilds):
        if user.get("id") == "demo" and guild_id == "demo-guild":
            pass # Allow demo user to select demo-guild
        else:
            raise HTTPException(status_code=403, detail="Access denied to this server")
    
    bot_guilds = await get_bot_guilds()
    if guild_id not in bot_guilds:
        # Check if it is a Discourse guild
        is_discourse = False
        for g in user_guilds:
            if str(g["id"]) == guild_id and g.get("is_discourse"):
                is_discourse = True
                break
        
        if not is_discourse:
            # If not bot guild AND not discourse guild -> error or redirect
            pass

    
    guild_name = "Unknown Server"
    guild_icon = None
    if guild_id == "demo-guild":
        guild_name = "Demo Server"
        guild_icon = None
    else:
        for g in user_guilds:
            if str(g["id"]) == str(guild_id):
                guild_name = g["name"]
                guild_icon = g.get("icon")
                break

    request.session["guild_id"] = guild_id
    request.session["guild_name"] = guild_name
    request.session["guild_icon"] = guild_icon
    return RedirectResponse(url="/", status_code=303)


@router.get("/add-discourse", response_class=HTMLResponse)
async def add_discourse_page(request: Request):
    # Přidání nového Discourse fóra
    user = request.session.get("discord_user")
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("add_discourse.html", {"request": request, "user": user})


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, start_date: str = None, end_date: str = None, role_id: str = None):
    try:
        return await _dashboard_logic(request, start_date, end_date, role_id)
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(err_msg)
        try:
            log_dir = os.path.join(ROOT_DIR, "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            with open(os.path.join(log_dir, "dashboard_crash.log"), "w") as f:
                f.write(err_msg)
        except Exception:
            pass
        
        if hasattr(e, "status_code"): raise e
        return HTMLResponse(content=f"""
        <html><body style="background:#111;color:#f88;font-family:monospace;padding:20px;">
        <h2>Internal Server Error</h2>
        <p>A critical error occurred while generating the dashboard. Please check the server logs for details.</p>
        </body></html>
        """, status_code=500)


@router.get("/features", response_class=HTMLResponse)
async def landing_features(request: Request):
    return templates.TemplateResponse("landing_features.html", {"request": request})


@router.get("/about", response_class=HTMLResponse)
async def landing_about(request: Request):
    
    stats = {"servers": "1", "users": "---", "uptime": "99.9%"}
    try:
        r = await get_redis_client()
        bot_guilds = await r.smembers("bot:guilds")
        
        total_msgs = 0
        total_users = 0
        
        for gid in bot_guilds:
            tm = await r.get(f"stats:total_msgs:{gid}") or "0"
            tu = await r.get(f"presence:total:{gid}") or "0"
            
            total_msgs += int(tm)
            total_users += int(tu)
            
        stats["servers"] = len(bot_guilds)
        stats["users"] = f"{total_users:,}".replace(",", " ")
        stats["messages"] = f"{total_msgs:,}".replace(",", " ")
        
    except Exception as e:
        print(f"Error fetching about stats: {e}")
        
    context = {"request": request, "stats": stats}
    return templates.TemplateResponse("landing_about.html", context)


@router.get("/privacy")
async def legal_privacy():
    return RedirectResponse(url="/docs/privacy")


@router.get("/terms")
async def legal_terms():
    return RedirectResponse(url="/docs/terms")


@router.get("/changelog")
async def docs_changelog():
    return RedirectResponse(url="/docs/changelog")


@router.get("/support")
async def support_page():
    return RedirectResponse(url="/docs/support")


@router.get("/commands", response_class=HTMLResponse)
async def commands_page(request: Request, _=Depends(require_auth)):
    sidebar_ctx = await get_sidebar_context(request)
    ctx = {"request": request}
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("docs/commands.html", ctx)


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, start_date: str = None, end_date: str = None, role_id: str = None):
    user = request.session.get("discord_user")
    if not user: return RedirectResponse(url="/")
    
    if request.session.get("role") == "guest":
        return RedirectResponse(url="/leaderboard")

    guild_id = request.session.get("guild_id")
    if not guild_id:
        return RedirectResponse(url="/select-server")

    if guild_id == "demo-guild":
        # SERVE MOCK DATA
        stats = get_demo_stats(start_date, end_date)
        sidebar_ctx = await get_sidebar_context(request)
        ctx = {
            "request": request,
            "user": user,
            **stats,
            "start_date": start_date or stats["start_date"],
            "end_date": end_date or stats["end_date"],
            "selected_role": role_id or "all",
            "roles": stats["roles"],
            "has_any_data": True,
            "widget_order": [
                "wow_card", "mom_card", "top_channels", "leaderboard", 
                "peak_analysis", "channel_dist", "commands", "voice_stats", 
                "traffic", "trend_analysis", "engagement", "export", "insights"
            ],
            "all_widgets": [
                ('wow_card', '📈 Trends (WoW)'),
                ('mom_card', '📊 Trends (MoM)'),
                ('top_channels', '🏆 Top Channels'),
                ('leaderboard', '👑 Leaderboard'),
                ('peak_analysis', '🔥 Peak Time'),
                ('channel_dist', '📢 Channel Dist'),
                ('commands', '🤖 Commands'),
                ('voice_stats', '🎙️ Voice Stats'),
                ('traffic', '🚦 Traffic'),
                ('trend_analysis', '📈 Growth Trend'),
                ('engagement', '🎯 Engagement'),
                ('export', '📤 Export Tools'),
                ('insights', '💡 Insights'),
                ('growth_chart', '📈 Member Growth'),
                ('hourly_chart', '⏰ Hourly Activity'),
                ('weekday_chart', '📅 Weekday Activity'),
                ('msg_len_chart', '📏 Msg Lengths'),
                ('weekend_chart', '🎉 Weekend Ratio'),
                ('xp_leaderboard', '🏆 XP Leaderboard')
            ]
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("analytics.html", ctx)

    guild_id = int(guild_id)

    
    from datetime import datetime, timedelta
    
    
    def_range = request.session.get("default_date_range", "last_30_days")
    def_role = request.session.get("default_role_id", "all")
    
    
    widget_order = request.session.get("analytics_order") or request.session.get("dashboard_order", [])
    
    
    
    
    if start_date is None or end_date is None:
        now = datetime.now()
        if def_range == "last_7_days":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        elif def_range == "last_30_days":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        elif def_range == "this_month":
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
        elif def_range == "all_time":
            start_date = "2023-01-01"
        else:
             
             start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        
        end_date = now.strftime("%Y-%m-%d")
    
    
    if role_id is None:
        role_id = def_role

    
    request.session["start_date"] = start_date
    request.session["end_date"] = end_date
    request.session["role_id"] = role_id
    
    
    DEFAULT_ORDER = [
        "wow_card", "mom_card", 
        "top_channels", "leaderboard", 
        "peak_analysis", 
        "channel_dist", "commands", "voice_stats", "traffic",
        "trend_analysis", "engagement", 
        "export", "insights"
    ]
    widget_order = request.session.get("dashboard_order", DEFAULT_ORDER)

    
    summary = await get_summary_card_data(guild_id=guild_id)
    has_any_data = summary["discord"]["msgs"] > 0

    
    from ..utils import get_cached_roles
    roles = await get_cached_roles(guild_id)
    roles_list = [(r["id"], r["name"]) for r in roles]

    
    sidebar_ctx = await get_sidebar_context(request)
    ctx = {
        "request": request,
        "user": user,
        "start_date": start_date,
        "end_date": end_date,
        "selected_role": role_id,
        "roles": roles_list,
        "has_any_data": has_any_data,
        "widget_order": request.session.get("analytics_order") or request.session.get("dashboard_order", DEFAULT_ORDER),
        "all_widgets": [
            ('wow_card', '📈 Trends (WoW)'),
            ('mom_card', '📊 Trends (MoM)'),
            ('top_channels', '🏆 Top Channels'),
            ('leaderboard', '👑 Leaderboard'),
            ('peak_analysis', '🔥 Peak Time'),
            ('channel_dist', '📢 Channel Dist'),
            ('commands', '🤖 Commands'),
            ('voice_stats', '🎙️ Voice Stats'),
            ('traffic', '🚦 Traffic'),
            ('trend_analysis', '📈 Growth Trend'),
            ('engagement', '🎯 Engagement'),
            ('export', '📤 Export Tools'),
            ('insights', '💡 Insights'),
            ('growth_chart', '📈 Member Growth'),
            ('hourly_chart', '⏰ Hourly Activity'),
            ('weekday_chart', '📅 Weekday Activity'),
            ('msg_len_chart', '📏 Msg Lengths'),
            ('weekend_chart', '🎉 Weekend Ratio'),
            ('xp_leaderboard', '🏆 XP Leaderboard')
        ]
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("analytics.html", ctx)


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, _=Depends(require_auth)):
    """User profile page with managed servers list."""
    user = request.session.get("discord_user", {})
    user_id = user.get("id")
    
    
    from ..utils import get_user_guilds, get_bot_guilds
    managed_guilds = await get_user_guilds(user_id)
    bot_guild_ids = set(await get_bot_guilds())
    
    
    
 
    
    
    servers = []
    for g in managed_guilds:
        is_active = str(g["id"]) in bot_guild_ids
        servers.append({
            "id": g["id"],
            "name": g["name"],
            "icon": g.get("icon"),
            "active": is_active,
            "dashboard_url": f"/activity?guild_id={g['id']}" if is_active else None,
            "invite_url": f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions=277025508352&scope=bot" if not is_active else None
        })
    
    # ADD DEMO GUILD FOR TESTING
    servers.append({
        "id": "demo-guild",
        "name": "Demo Server (CommunityMetrics)",
        "icon": "https://cdn.discordapp.com/embed/avatars/0.png",
        "active": True,
        "dashboard_url": "/activity?guild_id=demo-guild",
        "invite_url": None
    })

    
    current_guild_id = request.session.get("guild_id")
    current_guild_icon = request.session.get("guild_icon")
    
    if current_guild_id:
        
        matched_g = next((g for g in managed_guilds if str(g["id"]) == str(current_guild_id)), None)
        if not matched_g and request.session.get("guild_name"):
             matched_g = next((g for g in managed_guilds if g["name"] == request.session.get("guild_name")), None)
        
        if matched_g:
            current_guild_icon = matched_g.get("icon")
            
            if request.session.get("guild_icon") != current_guild_icon:
                request.session["guild_icon"] = current_guild_icon

    
    sidebar_ctx = await get_sidebar_context(request)
    ctx = {
        "request": request,
        "user": user,
        "role": request.session.get("role"),
        "servers": servers
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("profile.html", ctx)


@router.get("/activity", response_class=HTMLResponse)
async def activity_page(request: Request, guild_id: str = None, start_date: str = None, end_date: str = None, role_id: str = None, _=Depends(require_auth)):
    """Moderator Activity Page with manual Redis aggregation."""
    from ..utils import get_user_guilds
    
    user_role = request.session.get("role", "guest")
    user_id = request.session.get("discord_user", {}).get("id")
    
    
    if not guild_id:
        guild_id = request.session.get("guild_id")
    
    if guild_id == "demo-guild":
        # SERVE MOCK DATA
        stats = get_demo_stats(start_date, end_date)
        sidebar_ctx = await get_sidebar_context(request)
        ctx = {
            "request": request,
            "guild_id": guild_id,
            "activity": stats["activity_stats"],
            "deep_stats": stats["deep_stats"],
            "redis_stats": stats["redis_stats"],
            "warning": None,
            "user_role": user_role,
            "user": request.session.get("discord_user"),
            "daily_labels": stats.get("daily_labels", []),
            "daily_hours": stats.get("daily_hours", []),
            "leaderboard": stats["deep_stats"].get("leaderboard", []),
            "total_hours_30d": stats["deep_stats"].get("total_hours_30d", 0),
            "active_staff_count": stats["deep_stats"].get("active_staff_count", 0),
            "top_action": stats["deep_stats"].get("top_action", "N/A"),
            "start_date": start_date or stats["start_date"],
            "end_date": end_date or stats["end_date"],
            "roles": stats["roles"],
            "selected_role": role_id or "all",
            "widget_order": request.session.get("activity_order", []),
            "widget_spans": request.session.get("dashboard_spans", {})
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("activity.html", ctx)

    user_guilds = await get_user_guilds(user_id)
    target_guild_id = guild_id or request.session.get("active_guild_id")
    
    if not target_guild_id and user_guilds:
        target_guild_id = str(user_guilds[0]["id"]) 

    
    if start_date:
        request.session["start_date"] = start_date
    else:
        start_date = request.session.get("start_date", "2025-12-21")
        
    if end_date:
        request.session["end_date"] = end_date
    else:
        end_date = request.session.get("end_date", "2026-01-20")
    
    
    if user_role != "admin":
        if user_role == "mod":
            user_guilds = await get_user_guilds(user_id)
            managed_ids = [g["id"] for g in user_guilds]
            
            
            if target_guild_id not in managed_ids:
                 return templates.TemplateResponse("activity_restricted.html", {
                    "request": request,
                    "message": "Nemáte práva moderátora pro zobrazení statistik této guildy."
                })
            
            sidebar_ctx = await get_sidebar_context(request)
            
            
            ctx = {
                "request": request,
                "message": "Přístup k této stránce je omezen. Nemáte moderátorská práva."
            }
            ctx.update(sidebar_ctx)
            return templates.TemplateResponse("activity_restricted.html", ctx)
    
    
    
    from ..utils import get_activity_stats, get_redis_dashboard_stats, get_deep_stats_redis
    
    
    activity_stats = await get_activity_stats(int(target_guild_id), start_date=start_date, end_date=end_date)
    
    
    deep_stats = await get_deep_stats_redis(int(target_guild_id), start_date=start_date, end_date=end_date, role_id=role_id)
    
    
    redis_stats = await get_redis_dashboard_stats(int(target_guild_id), start_date=start_date, end_date=end_date)
    
    
    from datetime import datetime as dt, timedelta
    import json
    
    if start_date:
        try: d_start = dt.strptime(start_date, "%Y-%m-%d")
        except: d_start = dt.now() - timedelta(days=30)
    else:
        d_start = dt.now() - timedelta(days=30)
        
    if end_date:
        try: d_end = dt.strptime(end_date, "%Y-%m-%d")
        except: d_end = dt.now()
    else:
        d_end = dt.now()
        
    
    
    warning_msg = None

    
    sidebar_ctx = await get_sidebar_context(request)
    
    
    from ..utils import get_cached_roles
    roles = await get_cached_roles(int(target_guild_id))
    roles_list = [(r["id"], r["name"]) for r in roles]

    ctx = {
        "request": request,
        "guild_id": target_guild_id,
        "activity": activity_stats,
        "deep_stats": deep_stats,
        "redis_stats": redis_stats,
        "warning_msg": warning_msg,
        "user_role": user_role,
        "user": request.session.get("discord_user"),
        
        
        "daily_labels": deep_stats.get("daily_labels", []),
        "daily_hours": deep_stats.get("daily_weighted_hours", []), 
        "leaderboard": deep_stats.get("leaderboard", []),
        "total_hours_30d": deep_stats.get("total_hours_30d", 0),
        "active_staff_count": deep_stats.get("active_staff_count", 0),
        "top_action": deep_stats.get("top_action", "-"),
        "roles": roles_list,
        "selected_role": role_id or "all",
        "start_date": start_date or d_start.strftime("%Y-%m-%d"),
        "end_date": end_date or d_end.strftime("%Y-%m-%d"),
        "warning": warning_msg,
        "widget_order": request.session.get("activity_order", []),
        "widget_spans": request.session.get("dashboard_spans", {})
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("activity.html", ctx)


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request, _=Depends(require_auth)):
    """Render XP Leaderboard page."""
    user = request.session.get("discord_user", {})
    guild_id = request.session.get("guild_id")
    if not guild_id:
        return RedirectResponse(url="/select-server")
    
    if guild_id == "demo-guild":
        # SERVE MOCK DATA
        stats = get_demo_stats()
        sidebar_ctx = await get_sidebar_context(request)
        
        # Format demo leaderboard like the real one
        demo_leaderboard = []
        for i, entry in enumerate(stats["deep_stats"]["leaderboard"], 1):
            demo_leaderboard.append({
                "rank": i,
                "user_id": f"demo-{i}",
                "name": entry.get("username") or entry.get("name") or "Unknown User",
                "username": entry.get("username") or entry.get("name") or "Unknown User",
                "avatar": None,
                "xp": (10 - i) * 1000,
                "level": 10 - i,
                "progress": 50
            })
            
        ctx = {
            "request": request,
            "leaderboard": demo_leaderboard,
            "user_rank": None
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("leaderboard.html", ctx)

    guild_id = int(guild_id)
    
    
    r = await get_redis_client()
    key = f"levels:xp:{guild_id}"
    
    top_users = await r.zrevrange(key, 0, -1, withscores=True)
    
    leaderboard_data = []
    
    
    
    xp_conf = await r.hgetall("config:xp_formula")
    CA = int(xp_conf.get("a", 50))
    CB = int(xp_conf.get("b", 200))
    CC = int(xp_conf.get("c", 100))

    import math
    current_rank = 1
    for i, (uid, xp) in enumerate(top_users, 1):
        user_info = await r.hgetall(f"user:info:{uid}") or {}
        xp = int(xp)
        
        
        
        level = 0
        if xp >= CC:
             a, b, c = CA, CB, CC - xp
             d = (b**2) - (4*a*c)
             if d >= 0:
                 level = int((-b + math.sqrt(d)) / (2*a))
        
        
        current_level_xp = CA * (level**2) + CB * level + CC
        next_level_xp = CA * ((level+1)**2) + CB * (level+1) + CC
        
        
        xp_needed = next_level_xp - current_level_xp
        xp_progress = xp - current_level_xp
        
        
        if xp_needed <= 0: xp_needed = 1
        progress_pct = min(100, max(0, int((xp_progress / xp_needed) * 100)))

        
        display_name = user_info.get("username") or user_info.get("name")
        
        
        if not display_name or display_name == "Deleted User":
             continue
        
        leaderboard_data.append({
            "rank": current_rank,
            "user_id": uid,
            "username": display_name,
            "avatar": user_info.get("avatar"),
            "xp": xp,
            "level": level,
            "progress": progress_pct,
            "next_level_xp": int(next_level_xp)
        })
        current_rank += 1

    
    sidebar_ctx = await get_sidebar_context(request)
    
    ctx = {
        "request": request,
        "user": user,
        "leaderboard": leaderboard_data
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("leaderboard.html", ctx)


@router.get("/activity/user/{uid}", response_class=HTMLResponse)
async def user_activity_page(request: Request, uid: str, start_date: str = None, end_date: str = None, _=Depends(require_auth)):
    """Detailed activity page for a specific user."""
    
    
    today = datetime.now().date()
    try:
        if start_date:
            d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            d_start = today - timedelta(days=30)
            
        if end_date:
            d_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            d_end = today
    except ValueError:
        d_start = today - timedelta(days=30)
        d_end = today

    if str(uid).startswith("demo-") or request.session.get("guild_id") == "demo-guild":
        data = get_demo_user_activity(uid)
        sidebar_ctx = await get_sidebar_context(request)
        ctx = {
            "request": request,
            "user_info": data["user_info"],
            "days": data["days"],
            "values": data["values"],
            "is_bot": False,
            "summary": data["summary"]
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("user_activity.html", ctx)

    user_info = {"name": f"User {uid}", "avatar": "", "roles": []}
    daily_stats = {} 
    
    stats_summary = defaultdict(float) 
    
    try:
        r = await get_redis_client()
        user_session = request.session.get("discord_user")
        if not user_session:
             return RedirectResponse(url="/")
        
        # Try to get from query param or session
        gid = request.query_params.get("guild_id")
        if not gid:
             gid = request.session.get("active_guild_id")
        
        if not gid:
             return RedirectResponse(url="/select-server")
        
        
        info = await r.hgetall(f"user:info:{uid}")
        if info:
            user_info["name"] = info.get("name", f"User {uid}")
            user_info["avatar"] = info.get("avatar", "")
            if "roles" in info and info["roles"]:
                
                role_ids = info["roles"].split(",")
                all_roles = await r.hgetall(f"guild:roles:{gid}")
                user_info["roles"] = [all_roles.get(rid, f"Role {rid}") for rid in role_ids if rid in all_roles]

        
        weights = await get_action_weights(r)
        
        current_day = d_start
        while current_day <= d_end:
            day_str = current_day.strftime("%Y-%m-%d")
            
            daily_data = await get_daily_stats(r, gid, uid, current_day)
            
            if daily_data:
                
                for metric, val in daily_data.items():
                    if metric != "_version":
                        stats_summary[metric] += val
                
                
                chat_t = daily_data.get("chat_time", 0)
                voice_t = daily_data.get("voice_time", 0)
                
                action_t = 0
                for action_metric in ["bans", "kicks", "timeouts", "unbans", "verifications", "msg_deleted", "role_updates"]:
                    action_t += daily_data.get(action_metric, 0) * weights.get(action_metric, 0)
                
                weighted_total = chat_t + voice_t + action_t
                
                if day_str not in daily_stats: daily_stats[day_str] = 0
                daily_stats[day_str] += weighted_total
            
            current_day += timedelta(days=1)

        pass
    except Exception as e:
        print(f"Error fetching user activity: {e}")

    
    sorted_days = sorted(daily_stats.keys())
    daily_labels = [d[5:] for d in sorted_days]
    daily_values = [round(daily_stats[d] / 3600, 1) for d in sorted_days]
    
    
    chat_h = round(stats_summary["chat_time"] / 3600, 1)
    voice_h = round(stats_summary["voice_time"] / 3600, 1)
    
    total_weighted = 0
    for m, val in stats_summary.items():
        w = weights.get(m, 1)
        if m == "messages": w = 0
        total_weighted += (val * w)
        
    total_h = round(total_weighted / 3600, 1)
    
    action_breakdown = {
        "Bans": int(stats_summary["bans"]),
        "Kicks": int(stats_summary["kicks"]),
        "Timeouts": int(stats_summary["timeouts"]),
        "Unbans": int(stats_summary["unbans"]),
        "Verifications": int(stats_summary["verifications"]),
        "Deleted Msgs": int(stats_summary["msg_deleted"]),
        "Role Updates": int(stats_summary["role_updates"])
    }
    
    total_actions = sum(action_breakdown.values())

    
    sidebar_ctx = await get_sidebar_context(request)
    
    ctx = {
        "request": request,
        "user_info": user_info,
        "days": sorted_days,
        "values": daily_values,
        "is_bot": user_info.get("bot", False),
        "summary": {
            "total_h": total_h,
            "chat_h": chat_h,
            "voice_h": voice_h,
            "actions": total_actions,
            "breakdown": action_breakdown
        }
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("user_activity.html", ctx)


@router.get("/predictions")
async def predictions_page(request: Request, _=Depends(require_auth)):
    
    sidebar_ctx = await get_sidebar_context(request)
    context = {
        "request": request,
        "widget_order": request.session.get("predictions_order", [])
    }
    context.update(sidebar_ctx)
    return templates.TemplateResponse("predictions.html", context)

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

    # Restrict guest users (demo role has full read access)
    role = request.session.get("role")
    if role == "guest" and request.session.get("guild_id") != "demo-guild":
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
    
    
    from ..utils import get_dashboard_permissions
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

    
    
    
    from ..utils import get_cached_roles
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





