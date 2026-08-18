from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import time

from shared.community_health import api_key_digest, generate_api_key, normalise_config
from shared.redis_client import get_redis_client
from ..services.community_health_service import CommunityHealthService
from ..utils import get_sidebar_context
from ..demo_data import get_demo_health_overview, get_demo_health_evidence

router = APIRouter(tags=["community-health"])
templates = Jinja2Templates(directory="web/frontend/templates")


def require_auth(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(401, "Not authenticated")
    if request.session.get("role") == "guest":
        raise HTTPException(403, "Guest access is not allowed")
    return True


def selected_guild(request: Request) -> str:
    gid = request.session.get("guild_id")
    if not gid:
        raise HTTPException(400, "No guild selected")
    return str(gid)


def require_admin_session(request: Request):
    require_auth(request)
    if request.session.get("role") != "admin":
        raise HTTPException(403, "Administrator access required")
    return True


class RoleReviewInput(BaseModel):
    user_id: str = Field(min_length=1, max_length=30)
    judgement: Literal["observe", "discuss", "not_now", "recommended_by_team"]
    note: str = Field(default="", max_length=2000)


class ApiKeyInput(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    scopes: List[Literal["overview", "channels", "moderation", "help", "departures", "events", "role_evidence"]] = Field(default_factory=lambda: ["overview"])


async def _service() -> CommunityHealthService:
    return CommunityHealthService(await get_redis_client())


@router.get("/community-health", response_class=HTMLResponse)
async def community_health_page(request: Request, _=Depends(require_auth)):
    gid = selected_guild(request)
    service = await _service()
    sidebar = await get_sidebar_context(request)
    context = {
        "request": request,
        "user": request.session.get("discord_user"),
        "guild_id": gid,
        "config": await service.config(gid),
        "is_admin": request.session.get("role") == "admin",
        "csrf_token": request.session.get("csrf_token", ""),
        "widget_order": request.session.get("health_order", []),
        "widget_spans": request.session.get("dashboard_spans", {})
    }
    context.update(sidebar)
    return templates.TemplateResponse("community_health.html", context)


@router.get("/api/community-health/overview")
async def health_overview(request: Request, days: int = 30, _=Depends(require_auth)):
    guild_id = selected_guild(request)
    if guild_id == "demo-guild":
        return get_demo_health_overview()
    return await (await _service()).overview(guild_id, max(1, min(days, 365)))


@router.get("/api/community-health/conflicts")
async def health_conflicts(request: Request, days: int = 30, _=Depends(require_auth)):
    return await (await _service()).conflict_summary(selected_guild(request), days=max(1, min(days, 365)))


@router.get("/api/community-health/help-requests")
async def health_help(request: Request, days: int = 30, _=Depends(require_auth)):
    return await (await _service()).help_requests(selected_guild(request), days=max(1, min(days, 365)))


@router.get("/api/community-health/departures")
async def health_departures(request: Request, days: int = 30, _=Depends(require_auth)):
    return await (await _service()).departures(selected_guild(request), days=max(1, min(days, 365)))


@router.get("/api/community-health/moderator-workload")
async def health_workload(request: Request, days: int = 30, _=Depends(require_auth)):
    return await (await _service()).moderator_workload(selected_guild(request), days=max(1, min(days, 365)))


@router.get("/api/community-health/events")
async def health_events(request: Request, _=Depends(require_auth)):
    return await (await _service()).event_conversion(selected_guild(request))


@router.get("/api/community-health/role-evidence/{user_id}")
async def health_role_evidence(request: Request, user_id: str, days: int = 90, _=Depends(require_auth)):
    guild_id = selected_guild(request)
    if guild_id == "demo-guild":
        return get_demo_health_evidence(user_id)
    return await (await _service()).role_evidence(guild_id, user_id, max(1, min(days, 365)))


@router.post("/api/community-health/role-review")
async def save_role_review(request: Request, payload: RoleReviewInput, _=Depends(require_admin_session)):
    gid = selected_guild(request)
    reviewer = request.session.get("discord_user", {}).get("id", "")
    r = await get_redis_client()
    await r.hset(f"health:role_review:{gid}:{payload.user_id}", mapping={
        "judgement": payload.judgement,
        "note": payload.note,
        "reviewed_by": str(reviewer),
        "reviewed_at": datetime.now().isoformat(),
    })
    return {"status": "ok", "evidence": await CommunityHealthService(r).role_evidence(gid, payload.user_id)}


@router.post("/settings/community-health")
async def save_health_settings(
    request: Request,
    community_type: str = Form("general"),
    help_requests_enabled: Optional[str] = Form(None),
    moderation_context_enabled: Optional[str] = Form(None),
    departure_context_enabled: Optional[str] = Form(None),
    event_conversion_enabled: Optional[str] = Form(None),
    question_mode: str = Form("heuristic"),
    help_timeout_hours: int = Form(24),
    conflict_window_days: int = Form(30),
    support_channel_ids: str = Form(""),
    csrf_token: str = Form(""),
    _=Depends(require_admin_session),
):
    session_csrf = request.session.get("csrf_token", "")
    if session_csrf and not secrets.compare_digest(session_csrf, csrf_token):
        raise HTTPException(403, "Invalid CSRF token")
    gid = selected_guild(request)
    cfg = normalise_config({
        "community_type": community_type,
        "help_requests_enabled": help_requests_enabled == "on",
        "moderation_context_enabled": moderation_context_enabled == "on",
        "departure_context_enabled": departure_context_enabled == "on",
        "event_conversion_enabled": event_conversion_enabled == "on",
        "question_mode": question_mode if question_mode in {"heuristic", "all"} else "heuristic",
        "help_timeout_hours": help_timeout_hours,
        "conflict_window_days": conflict_window_days,
    })
    r = await get_redis_client()
    await r.hset(f"cfg:health:{gid}", mapping={k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in cfg.items()})
    channel_ids = {part.strip() for part in support_channel_ids.replace(";", ",").split(",") if part.strip().isdigit()}
    key = f"cfg:health:support_channels:{gid}"
    await r.delete(key)
    if channel_ids:
        await r.sadd(key, *channel_ids)
    return RedirectResponse("/community-health", status_code=303)


@router.post("/api/community-health/api-keys")
async def create_api_key(request: Request, payload: ApiKeyInput, _=Depends(require_admin_session)):
    gid = selected_guild(request)
    raw_key = generate_api_key()
    digest = api_key_digest(raw_key)
    r = await get_redis_client()
    await r.hset(f"api:key:{digest}", mapping={
        "guild_id": gid,
        "label": payload.label,
        "scopes": ",".join(sorted(set(payload.scopes))),
        "created_by": str(request.session.get("discord_user", {}).get("id", "")),
        "created_at": datetime.now().isoformat(),
        "enabled": "1",
    })
    await r.sadd(f"api:keys:guild:{gid}", digest)
    return {"api_key": raw_key, "label": payload.label, "scopes": payload.scopes, "notice": "Klíč se zobrazí pouze nyní."}


@router.get("/api/community-health/api-keys")
async def list_api_keys(request: Request, _=Depends(require_admin_session)):
    gid = selected_guild(request)
    r = await get_redis_client()
    rows = []
    for digest in await r.smembers(f"api:keys:guild:{gid}"):
        item = await r.hgetall(f"api:key:{digest}")
        if item:
            rows.append({"id": digest[:12], "label": item.get("label"), "scopes": item.get("scopes", "").split(","), "created_at": item.get("created_at"), "enabled": item.get("enabled") == "1"})
    return rows


@router.delete("/api/community-health/api-keys/{key_id}")
async def revoke_api_key(request: Request, key_id: str, _=Depends(require_admin_session)):
    gid = selected_guild(request)
    r = await get_redis_client()
    matches = [digest for digest in await r.smembers(f"api:keys:guild:{gid}") if digest.startswith(key_id)]
    if len(matches) != 1:
        raise HTTPException(404, "API key not found")
    digest = matches[0]
    await r.hset(f"api:key:{digest}", mapping={"enabled": "0", "revoked_at": datetime.now().isoformat()})
    return {"status": "revoked", "id": digest[:12]}


async def api_key_context(x_api_key: str = Header(..., alias="X-API-Key")) -> dict:
    r = await get_redis_client()
    digest = api_key_digest(x_api_key)
    item = await r.hgetall(f"api:key:{digest}")
    if not item or item.get("enabled") != "1":
        raise HTTPException(401, "Invalid API key")
    bucket = int(time.time() // 60)
    rate_key = f"api:rate:{digest}:{bucket}"
    count = await r.incr(rate_key)
    if count == 1:
        await r.expire(rate_key, 120)
    if count > 120:
        raise HTTPException(429, "API rate limit exceeded (120 requests/minute)")
    await r.hset(f"api:key:{digest}", "last_used_at", datetime.now().isoformat())
    item["scopes_set"] = set(filter(None, item.get("scopes", "").split(",")))
    return item


def require_scope(ctx: dict, scope: str):
    if scope not in ctx["scopes_set"] and "*" not in ctx["scopes_set"]:
        raise HTTPException(403, f"API key lacks '{scope}' scope")


@router.get("/api/v1/health/overview", tags=["public-api-v1"])
async def api_v1_overview(days: int = 30, ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "overview")
    return await (await _service()).overview(ctx["guild_id"], max(1, min(days, 365)))


@router.get("/api/v1/health/moderation/conflicts", tags=["public-api-v1"])
async def api_v1_conflicts(days: int = 30, ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "moderation")
    return await (await _service()).conflict_summary(ctx["guild_id"], days=max(1, min(days, 365)))


@router.get("/api/v1/health/help-requests", tags=["public-api-v1"])
async def api_v1_help(days: int = 30, ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "help")
    return await (await _service()).help_requests(ctx["guild_id"], days=max(1, min(days, 365)))


@router.get("/api/v1/health/departures", tags=["public-api-v1"])
async def api_v1_departures(days: int = 30, ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "departures")
    return await (await _service()).departures(ctx["guild_id"], days=max(1, min(days, 365)))


@router.get("/api/v1/health/events", tags=["public-api-v1"])
async def api_v1_events(ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "events")
    return await (await _service()).event_conversion(ctx["guild_id"])


@router.get("/api/v1/channels", tags=["public-api-v1"])
async def api_v1_channels(days: int = 30, ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "channels")
    from ..utils import get_channel_distribution
    gid = int(ctx["guild_id"])
    end = datetime.now()
    start = end - timedelta(days=max(1, min(days, 365)))
    rows = await get_channel_distribution(gid, start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))
    r = await get_redis_client()
    for row in rows:
        row["name"] = await r.hget(f"channel:info:{row.get('channel_id')}", "name") or f"Channel {row.get('channel_id')}"
    return {"items": rows}


@router.get("/api/v1/health/role-evidence/{user_id}", tags=["public-api-v1"])
async def api_v1_role_evidence(user_id: str, days: int = 90, ctx: dict = Depends(api_key_context)):
    require_scope(ctx, "role_evidence")
    return await (await _service()).role_evidence(ctx["guild_id"], user_id, max(1, min(days, 365)))
