from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict
import datetime
import pydantic
from .auth import VITE_DOCS_URL
from ..utils import (
    get_dashboard_team, get_dashboard_permissions, get_sidebar_context,
    get_action_weights, add_dashboard_user
)
from ..security import require_csrf
from ..core.container import AppContainer

class TeamUser(pydantic.BaseModel):
    user_id: str
    username: str
    avatar: Optional[str] = None
    permissions: List[str]

from ..utils import require_admin
router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="web/frontend/templates")

def require_auth(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True

@router.get("/api/settings/team")
async def get_team_api(request: Request):
    """Get list of team members."""
    await require_auth(request)
    guild_id = request.session.get("guild_id")
    if not guild_id: raise HTTPException(400, "No guild selected")

    if guild_id == "demo-guild":
        return [
            {"user_id": "demo-admin", "display_name": "Demo Admin", "roles": ["ADMIN"], "added_at": "2024-01-01"},
            {"user_id": "demo-mod", "display_name": "Demo Moderator", "roles": ["MOD"], "added_at": "2024-01-02"}
        ]
    
    
    
    user_id = request.session.get("discord_user", {}).get("id")
    role = request.session.get("role")
    
    perms = await get_dashboard_permissions(guild_id, user_id, role)
    if "*" not in perms and "manage_team" not in perms:
        raise HTTPException(403, "Insufficient permissions")
        
    team = await get_dashboard_team(guild_id)
    return team


@router.post("/api/settings/team")
async def add_team_member(request: Request, member: TeamUser):
    """Add or update a team member."""
    await require_auth(request)
    await require_csrf(request)
    guild_id = request.session.get("guild_id")
    
    user_id = request.session.get("discord_user", {}).get("id")
    role = request.session.get("role")
    
    perms = await get_dashboard_permissions(guild_id, user_id, role)
    if "*" not in perms and "manage_team" not in perms:
        raise HTTPException(403, "Insufficient permissions")
        
    success = await add_dashboard_user(
        guild_id, 
        member.user_id, 
        {"username": member.username, "avatar": member.avatar or ""},
        member.permissions
    )
    
    if success: return {"status": "ok"}
    else: raise HTTPException(500, "Failed to save user")


@router.get("/settings/team", response_class=HTMLResponse)
async def team_settings_page(request: Request, _=Depends(require_auth)):
    """Team Management Page."""
    guild_id = request.session.get("guild_id")
    if not guild_id: return RedirectResponse("/select-server")
    
    
    user_id = request.session.get("discord_user", {}).get("id")
    role = request.session.get("role")
    perms = await get_dashboard_permissions(guild_id, user_id, role)
    
    if "*" not in perms and "manage_team" not in perms:
        sidebar_ctx = await get_sidebar_context(request)
        ctx = {
            "request": request,
            "message": "Nemáte oprávnění spravovat tým."
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("activity_restricted.html", ctx)

    
    sidebar_ctx = await get_sidebar_context(request)
    
    ctx = {
        "request": request,
        "user": request.session.get("discord_user"),
        "current_perms": perms,
        "permissions_list": [
            {"id": "view_stats", "name": "Zobrazit Statistiky", "desc": "Read-only přístup k dashboardu"},
            {"id": "manage_settings", "name": "Spravovat Nastavení", "desc": "Úprava vah a nastavení bota"},
            {"id": "export_data", "name": "Export Dat", "desc": "Stahování CSV/JSON exportů"},
            {"id": "manage_team", "name": "Spravovat Tým", "desc": "Přidávání a odebírání uživatelů"}
        ]
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("team.html", ctx)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, _=Depends(require_auth)):
    """Main settings page. Demo users can view in read-only mode."""
    import secrets
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    role = request.session.get("role")
    if role not in ("admin", "demo"):
        raise HTTPException(status_code=403, detail="Přístup pouze pro administrátory")
    user = request.session.get("discord_user")
    guild_id = request.session.get("guild_id")

    if guild_id == "demo-guild":
        sidebar_ctx = await get_sidebar_context(request)
        ctx = {
            "request": request,
            "user": user,
            "guild_id": guild_id,
            "is_admin": True,
            "show_deleted_data": False,
            "default_date_range": "last_30_days",
            "default_role_id": "all",
            "roles": [(1, "Admin"), (2, "Moderator"), (3, "Member")],
            "weights": {
                "bans": 3600, "kicks": 1800, "timeouts": 600, "unbans": 1200, 
                "verifications": 300, "msg_deleted": 60, "role_updates": 300,
                "session_base": 180, "char_weight": 1, "reply_weight": 60, "msg_weight": 0,
                "chat_time": 1, "voice_time": 1
            },
            "xp_formula": {"a": 50, "b": 200, "c": 100, "min": 15, "max": 25, "voice_min": 5, "voice_max": 10},
            "security_weights": {"mod_ratio": 25, "security": 25, "engagement": 25, "moderation": 25},
            "security_ideals": {"mod_ratio_min": 50, "mod_ratio_max": 100, "dau_percent": 10}
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("settings.html", ctx)
    
    weights = {
        "bans": 300, "kicks": 180, "timeouts": 180, "unbans": 120, 
        "verifications": 120, "msg_deleted": 60, "role_updates": 30,
        "chat_time": 1, "voice_time": 1,
        "session_base": 180, "char_weight": 1, "reply_weight": 60, "msg_weight": 0
    }
    
    
    security_weights = {"mod_ratio": 25, "security": 25, "engagement": 25, "moderation": 25}
    security_ideals = {
        "mod_ratio_min": 50, "mod_ratio_max": 100,
        "dau_percent": 10, "mod_actions_min": 1, "mod_actions_max": 5,
        "verification_level": 2
    }
    
    
    xp_formula = {"a": 50, "b": 200, "c": 100}
    
    try:
        r = await get_redis_client()
        weights = await get_action_weights(r)
        
        
        stored_sec_weights = await r.hgetall("config:security_weights")
        if stored_sec_weights:
            for k, v in stored_sec_weights.items():
                security_weights[k] = int(v)
        
        stored_sec_ideals = await r.hgetall("config:security_ideals")
        if stored_sec_ideals:
            for k, v in stored_sec_ideals.items():
                security_ideals[k] = float(v) if '.' in str(v) else int(v)

        
        stored_xp = await r.hgetall("config:xp_formula")
        if stored_xp:
            xp_formula["a"] = int(stored_xp.get("a", 50))
            xp_formula["b"] = int(stored_xp.get("b", 200))
            xp_formula["c"] = int(stored_xp.get("c", 100))
            xp_formula["min"] = int(stored_xp.get("min", 15))
            xp_formula["max"] = int(stored_xp.get("max", 25))
            xp_formula["voice_min"] = int(stored_xp.get("voice_min", 5))
            xp_formula["voice_max"] = int(stored_xp.get("voice_max", 10))
            
    except Exception as e:
        print(f"Error loading settings: {e}")
        
        
    
    
    if guild_id == "demo-guild":
        sidebar_ctx = await get_sidebar_context(request)
        ctx = {
            "request": request,
            "user": request.session.get("discord_user"),
            "guild_id": guild_id,
            "is_admin": True,
            "show_deleted_data": False,
            "default_date_range": "last_30_days",
            "default_role_id": "all",
            "roles": [(1, "Admin"), (2, "Moderator"), (3, "Member")],
            "weights": weights,
            "xp_formula": xp_formula,
            "security_weights": security_weights,
            "security_ideals": security_ideals
        }
        ctx.update(sidebar_ctx)
        return templates.TemplateResponse("settings.html", ctx)

    roles_list = []
    guild_id = request.session.get("guild_id")
    if guild_id:
        from ..utils import get_cached_roles
        roles = await get_cached_roles(int(guild_id))
        roles_list = [(r["id"], r["name"]) for r in roles]

    
    sidebar_ctx = await get_sidebar_context(request)

    ctx = {
        "request": request, 
        "weights": weights,
        "show_deleted_data": request.session.get("show_deleted_data", False),
        "default_date_range": request.session.get("default_date_range", "last_30_days"),
        "default_role_id": request.session.get("default_role_id", "all"),
        "roles": roles_list,
        "security_weights": security_weights,
        "security_ideals": security_ideals,
        "xp_formula": xp_formula
    }
    ctx.update(sidebar_ctx)
    return templates.TemplateResponse("settings.html", ctx)


@router.post("/settings/general")
async def update_general_settings(
    request: Request, 
    show_deleted: Optional[str] = Form(None), 
    default_date_range: str = Form("last_30_days"),
    default_role_id: str = Form("all"),
    _=Depends(require_auth)
):
    """Update general settings in session."""
    await require_csrf(request)
    
    request.session["show_deleted_data"] = (show_deleted == "on")
    request.session["default_date_range"] = default_date_range
    request.session["default_role_id"] = default_role_id
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/settings/dashboard")
async def update_dashboard_layout(
    request: Request,
    show_comparisons: Optional[str] = Form(None),
    show_top_channels: Optional[str] = Form(None),
    show_leaderboard: Optional[str] = Form(None),
    show_peak_analysis: Optional[str] = Form(None),
    show_channel_dist: Optional[str] = Form(None),
    show_commands: Optional[str] = Form(None),
    show_voice: Optional[str] = Form(None),
    show_traffic: Optional[str] = Form(None),
    show_tools: Optional[str] = Form(None),
    widget_order: Optional[str] = Form(None),
    widget_spans: Optional[str] = Form(None),
    page: str = Form("analytics"),
    _=Depends(require_auth)
):
    """Update dashboard layout preferences in session."""
    await require_csrf(request)
    if page == "analytics":
        layout = {
            "show_comparisons": show_comparisons == "on",
            "show_top_channels": show_top_channels == "on",
            "show_leaderboard": show_leaderboard == "on",
            "show_peak_analysis": show_peak_analysis == "on",
            "show_channel_dist": show_channel_dist == "on",
            "show_commands": show_commands == "on",
            "show_voice": show_voice == "on",
            "show_traffic": show_traffic == "on",
            "show_tools": show_tools == "on"
        }
        request.session["dashboard_layout"] = layout
    
    
    if widget_spans:
        import json
        try:
            spans_dict = json.loads(widget_spans)
            current_spans = request.session.get("dashboard_spans", {})
            current_spans.update(spans_dict)
            request.session["dashboard_spans"] = current_spans
        except Exception as e:
            print(f"Invalid widget spans JSON: {e}")
    
    
    if widget_order:
        import json
        try:
            order_list = json.loads(widget_order)
            if page == "overview":
                request.session["overview_order"] = order_list
            elif page == "predictions":
                request.session["predictions_order"] = order_list
            elif page == "health":
                request.session["health_order"] = order_list
            elif page == "activity":
                request.session["activity_order"] = order_list
            else:
                request.session["analytics_order"] = order_list
                request.session["dashboard_order"] = order_list 
        except:
            print("Invalid widget order JSON")

    
    redirect_url = "/analytics"
    if page == "overview": redirect_url = "/"
    elif page == "predictions": redirect_url = "/predictions"
    elif page == "health": redirect_url = "/community-health"
    elif page == "activity": redirect_url = "/activity"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/settings/dashboard/reset")
async def reset_dashboard_layout(
    request: Request,
    page: str = Form("analytics"),
    _=Depends(require_auth)
):
    """Reset dashboard layout preferences to defaults."""
    await require_csrf(request)
    if page == "overview":
        if "overview_order" in request.session:
            del request.session["overview_order"]
    elif page == "predictions":
        if "predictions_order" in request.session:
            del request.session["predictions_order"]
    elif page == "health":
        if "health_order" in request.session:
            del request.session["health_order"]
    elif page == "activity":
        if "activity_order" in request.session:
            del request.session["activity_order"]
    else:
        if "analytics_order" in request.session:
            del request.session["analytics_order"]
        if "dashboard_order" in request.session:
            del request.session["dashboard_order"]
            
    # Also clear spans if we want a full reset
    if "dashboard_spans" in request.session:
        del request.session["dashboard_spans"]
        
    redirect_url = "/analytics"
    if page == "overview": redirect_url = "/"
    elif page == "predictions": redirect_url = "/predictions"
    elif page == "health": redirect_url = "/community-health"
    elif page == "activity": redirect_url = "/activity"
    
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/settings/security-score")
async def update_security_score_settings(
    request: Request,
    weight_mod_ratio: int = Form(25),
    weight_security: int = Form(25),
    weight_engagement: int = Form(25),
    weight_moderation: int = Form(25),
    ideal_mod_ratio_min: int = Form(50),
    ideal_mod_ratio_max: int = Form(100),
    ideal_dau_percent: int = Form(10),
    ideal_mod_actions_min: float = Form(1),
    ideal_mod_actions_max: float = Form(5),
    ideal_verification_level: int = Form(2),
    _=Depends(require_admin)
):
    """Update security score weights and ideals in Redis."""
    await require_csrf(request)
    try:
        r = await get_redis_client()
        
        
        await r.hset("config:security_weights", mapping={
            "mod_ratio": weight_mod_ratio,
            "security": weight_security,
            "engagement": weight_engagement,
            "moderation": weight_moderation
        })
        
        
        await r.hset("config:security_ideals", mapping={
            "mod_ratio_min": ideal_mod_ratio_min,
            "mod_ratio_max": ideal_mod_ratio_max,
            "dau_percent": ideal_dau_percent,
            "mod_actions_min": ideal_mod_actions_min,
            "mod_actions_max": ideal_mod_actions_max,
            "verification_level": ideal_verification_level
        })
        
    except Exception as e:
        print(f"Error saving security score settings: {e}")
        
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/settings/weights")
async def update_weights(
    request: Request,
    bans: int = Form(...), kicks: int = Form(...), timeouts: int = Form(...),
    unbans: int = Form(...), verifications: int = Form(...), 
    msg_deleted: int = Form(...), role_updates: int = Form(...),
    chat_time: int = Form(...), voice_time: int = Form(...),
    session_base: int = Form(180), char_weight: int = Form(1),
    reply_weight: int = Form(60), msg_weight: int = Form(0),
    _=Depends(require_admin)
):
    """Update action weights in Redis."""
    await require_csrf(request)
    try:
        r = await get_redis_client()
        
        mapping = {
            "bans": bans, "kicks": kicks, "timeouts": timeouts,
            "unbans": unbans, "verifications": verifications,
            "msg_deleted": msg_deleted, "role_updates": role_updates,
            "chat_time": chat_time, "voice_time": voice_time,
            "session_base": session_base, "char_weight": char_weight,
            "reply_weight": reply_weight, "msg_weight": msg_weight
        }
        
        await r.hset("config:action_weights", mapping=mapping)
        
        
        await r.incr("config:weights_version")
        
        pass
        
    except Exception as e:
        print(f"Error saving weights: {e}")
        
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/settings/xp-formula")
async def update_xp_formula(
    request: Request,
    xp_a: int = Form(...),
    xp_b: int = Form(...),
    xp_c: int = Form(...),
    xp_min: int = Form(15),
    xp_max: int = Form(25),
    xp_voice_min: int = Form(5),
    xp_voice_max: int = Form(10),
    _=Depends(require_admin)
):
    """Update XP formula coefficients in Redis."""
    await require_csrf(request)
    try:
        r = await get_redis_client()
        await r.hset("config:xp_formula", mapping={
            "a": xp_a,
            "b": xp_b,
            "c": xp_c,
            "min": xp_min,
            "max": xp_max,
            "voice_min": xp_voice_min,
            "voice_max": xp_voice_max
        })
    except Exception as e:
        print(f"Error saving XP formula: {e}")
    
    return RedirectResponse(url="/settings", status_code=303)
