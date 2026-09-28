from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response
from typing import Optional
from fastapi.responses import JSONResponse
import datetime

router = APIRouter(tags=["api"])

from ..utils import *
from ..demo_data import get_demo_stats
from ..security import require_csrf
@router.post("/api/admin/config/bot-token")
async def set_bot_token(request: Request, token: str = Form(...), _=Depends(require_admin)):
    # Nastavení Discord bot tokenu systémovým administrátorem
    await require_csrf(request)

    if not token or len(token) < 30:
        return JSONResponse({"error": "Neplatný token"}, status_code=400)

    await update_env_token(token)
    return JSONResponse({"success": True, "message": "Token byl úspěšně uložen. Bot se brzy spustí."})

@router.post("/api/discourse/add")
async def api_add_discourse(
    request: Request,
    url: str = Form(...),
    api_key: str = Form(...),
    api_user: str = Form(...)
):
    await require_csrf(request)

    # API pro přidání Discourse
    user = request.session.get("discord_user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # SSRF & DNS Rebinding Protection. The same check runs again before every
    # later background sync (scripts/discourse_sync.py), since DNS records can
    # change after the instance was added here.
    from urllib.parse import urlparse
    from shared.net_security import assert_safe_discourse_url, validate_hostname_ips, UnsafeDiscourseURLError

    try:
        url = assert_safe_discourse_url(url)
    except UnsafeDiscourseURLError as e:
        return JSONResponse({"error": str(e)}, status_code=403 if "SSRF" in str(e) else 400)

    parsed_url = urlparse(url)

    # Verify connection to Discourse
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{url}/site.json",
                headers={"Api-Key": api_key, "Api-Username": api_user},
                follow_redirects=False # Prevent SSRF via redirects
            )

            # Post-Fetch DNS Rebinding Validation
            if not validate_hostname_ips(parsed_url.hostname):
                return JSONResponse({"error": "SSRF Protection: DNS Rebinding detected"}, status_code=403)

            if resp.status_code != 200:
                 return JSONResponse({"error": f"Failed to connect: {resp.status_code}"}, status_code=400)

            site_data = resp.json()
            title = site_data.get("title", "Discourse Forum")
            icon = ""
    except Exception as e:
        return JSONResponse({"error": f"Connection error: {str(e)}"}, status_code=400)

    # connection ok -> generate ID and save
    try:
        r = await get_redis_client()

        # Generate a unique psuedo-snowflake ID (negative to distinguish from Discord?)
        # Or just a large random int. Let's use negative timestamps to be safe and easy
        import time
        guild_id = int(time.time() * 1000) * -1

        # Save config
        conf_key = f"discourse:conf:{guild_id}"
        await r.hset(conf_key, mapping={
            "url": url,
            "api_key": api_key,
            "api_user": api_user,
            "name": title,
            "icon_url": icon,
            "created_by": user["id"]
        })

        # Link to user
        await r.sadd(f"user:discourse:{user['id']}", guild_id)

        # Add to global list
        await r.sadd("discourse:ids", guild_id)

        # Add to backfill queue so that discourse_sync.py will download its history
        await r.lpush("discourse:backfill_queue", guild_id)

        return JSONResponse({"status": "ok", "guild_id": str(guild_id)})

    except Exception as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)

try:
    from scripts.discourse_sync import DiscourseSync
except ImportError:
    DiscourseSync = None

@router.post("/api/discourse/sync")
async def api_trigger_sync(request: Request, guild_id: str = Form(...)):
    # Ruční spuštění synchronizace s Discoursem
    user = request.session.get("discord_user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await require_csrf(request)

    r = await get_redis_client()
    is_owner = await r.sismember(f"user:discourse:{user['id']}", guild_id)
    if not is_owner and request.session.get("role") != "admin":
         return JSONResponse({"error": "Permission denied"}, status_code=403)

    if not DiscourseSync:
        return JSONResponse({"error": "Sync script not available"}, status_code=500)

    try:
        syncer = DiscourseSync()
        await syncer.sync_guild(guild_id)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/api/settings/team/{target_id}")
async def remove_team_member(request: Request, target_id: str):
    """Remove a team member."""
    await require_auth(request)
    await require_csrf(request)
    guild_id = request.session.get("guild_id")

    user_id = request.session.get("discord_user", {}).get("id")
    role = request.session.get("role")

    perms = await get_dashboard_permissions(guild_id, user_id, role)
    if "*" not in perms and "manage_team" not in perms:
        raise HTTPException(403, "Insufficient permissions")

    success = await remove_dashboard_user(guild_id, target_id)
    return {"status": "ok" if success else "error"}

@router.get("/api/leaderboard/xp")
async def get_xp_leaderboard(request: Request, _=Depends(require_view_stats)):
    """Get XP Leaderboard."""
    await require_auth(request)
    guild_id = request.session.get("guild_id")
    if not guild_id: raise HTTPException(400, "No guild selected")

    if guild_id == "demo-guild":
        return JSONResponse([
            {"user_id": f"demo-{i}", "username": f"Demo User {i}", "display_name": f"Demo User {i}", "xp": (100 - i) * 1000, "level": 100 - i, "rank": i, "avatar": None}
            for i in range(1, 101)
        ])

    r = await get_redis_client()
    key = f"levels:xp:{guild_id}"

    top_users = await r.zrevrange(key, 0, 99, withscores=True)

    data = []

    current_rank = 1
    for i, (uid, xp) in enumerate(top_users, 1):
        user_info = await r.hgetall(f"user:info:{uid}") or {}
        username = user_info.get("username", "Unknown")

        if username == "Deleted User":
            continue

        xp = int(xp)
        level = 0
        if xp >= 100:

             import math
             a, b, c = 5, 50, 100 - xp
             d = (b**2) - (4*a*c)
             if d >= 0:
                 level = int((-b + math.sqrt(d)) / (2*a))

        data.append({
            "rank": current_rank,
            "user_id": uid,
            "username": username,
            "avatar": user_info.get("avatar"),
            "xp": xp,
            "level": level
        })
        current_rank += 1

    return data

@router.get("/api/predictions-data")
async def get_predictions_data(request: Request, _=Depends(require_auth)):
    guild_id = request.session.get("guild_id")
    if not guild_id: return JSONResponse({"status": "error"}, status_code=400)

    if guild_id == "demo-guild":
        from ..demo_data import get_demo_predictions_data
        return JSONResponse(get_demo_predictions_data())

    if not await has_dashboard_permission(request, "view_stats"):
        raise HTTPException(status_code=403, detail="Nemáte oprávnění pro tuto akci.")

    from ..utils import load_member_stats, get_redis, get_activity_stats
    import datetime

    end_dt = datetime.datetime.now()
    r = await get_redis()

    current_members_str = await r.get(f"presence:total:{guild_id}")
    if not current_members_str:
        current_members_str = await r.get(f"stats:total_members:{guild_id}")
    current_members = int(current_members_str) if current_members_str else 0

    stats = await load_member_stats(guild_id)
    joins_history = stats.get('joins', [])
    leaves_history = stats.get('leaves', [])
    dates = stats.get('labels', [])

    recent_months = 12
    recent_joins = joins_history[-recent_months:] if len(joins_history) >= recent_months else joins_history
    recent_leaves = leaves_history[-recent_months:] if len(leaves_history) >= recent_months else leaves_history

    if recent_joins:
        avg_monthly_joins = sum(recent_joins) / len(recent_joins)
        avg_monthly_leaves = sum(recent_leaves) / len(recent_leaves) if recent_leaves else 0
        avg_monthly_growth = avg_monthly_joins - avg_monthly_leaves
    else:
        avg_monthly_growth = 0
        avg_monthly_joins = 0
        avg_monthly_leaves = 0

    from ..utils import get_health_research_data
    research_data = await get_health_research_data(guild_id)

    if research_data.get("success"):
        p_stay_active = research_data.get("retention_pct", 0) / 100.0 if research_data.get("retention_pct") is not None else 0
        p_inactive = research_data.get("inactivity_risk_pct", 0) / 100.0 if research_data.get("inactivity_risk_pct") is not None else 0
        predicted_growth_30d = round(avg_monthly_growth)
        predicted_members_30d = current_members + predicted_growth_30d
    else:
        predicted_growth_30d = round(avg_monthly_growth)
        predicted_members_30d = current_members + predicted_growth_30d

    # Růst v procentech
    growth_pct = round((predicted_growth_30d / max(1, current_members) * 100), 2)

    forecast_dates = []
    forecast_members = []

    running_total = current_members
    for i in range(1, 7):
        future_date = end_dt + datetime.timedelta(days=30*i)
        forecast_dates.append(future_date.strftime("%Y-%m"))
        running_total += round(avg_monthly_growth)
        forecast_members.append(running_total)

    history_dates = dates[-12:] if len(dates) > 12 else dates
    history_members = stats.get('total', [])[-12:] if len(stats.get('total', [])) > 12 else stats.get('total', [])

    if not history_members:
        history_members = [current_members]
        history_dates = [end_dt.strftime("%Y-%m")]

    from ..utils import get_redis
    r = await get_redis()

    activity_history = []
    hist_dates = []

    global_first_seen = end_dt.timestamp()
    async for key in r.scan_iter(f"events:msg:{guild_id}:*"):
        msgs = await r.zrange(key, 0, 0, withscores=True)
        if msgs:
            ts = float(msgs[0][1])
            if ts < global_first_seen:
                global_first_seen = ts

    first_date = datetime.datetime.fromtimestamp(global_first_seen).date()

    for i in range(30):
        d = end_dt - datetime.timedelta(days=29-i)
        d_str = d.strftime("%Y%m%d")

        if d.date() < first_date:
            continue

        h_data = await r.hgetall(f"stats:hourly:{guild_id}:{d_str}")
        daily_sum = sum(int(float(v)) for v in h_data.values())
        activity_history.append(daily_sum)
        hist_dates.append(d)

    act_x = list(range(len(activity_history)))
    act_y = activity_history
    n_act = len(act_y)

    if n_act > 1:
        s_x = sum(act_x)
        s_y = sum(act_y)
        s_xy = sum(i*j for i, j in zip(act_x, act_y))
        s_xx = sum(i*i for i in act_x)
        try:
            act_slope = (n_act*s_xy - s_x*s_y) / (n_act*s_xx - s_x**2)
            act_intercept = (s_y - act_slope*s_x) / n_act
        except:
            act_slope = 0
            act_intercept = sum(act_y)/n_act
    else:
        act_slope = 0
        act_intercept = 0

    weekday_totals = [0] * 7
    weekday_counts = [0] * 7

    for i, val in enumerate(activity_history):
        wd = hist_dates[i].weekday()
        weekday_totals[wd] += val
        weekday_counts[wd] += 1

    global_avg = sum(activity_history) / n_act if n_act > 0 else 1
    if global_avg == 0: global_avg = 1

    seasonality_indices = []
    for d in range(7):
        avg_for_day = weekday_totals[d] / weekday_counts[d] if weekday_counts[d] > 0 else global_avg

        seasonality_indices.append(avg_for_day / global_avg)

    today_weekday = end_dt.weekday()
    forecast_activity = []
    forecast_day_labels = []
    cz_days = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

    for i in range(1, 8):

        future_x = (n_act - 1) + i

        trend_level = act_slope * future_x + act_intercept
        if trend_level < 0: trend_level = 0

        future_wd = (today_weekday + i) % 7
        seasonal_adjust = seasonality_indices[future_wd]

        final_pred = trend_level * seasonal_adjust

        forecast_activity.append(round(final_pred))
        forecast_day_labels.append(cz_days[future_wd])

    expected_msgs_tomorrow = forecast_activity[0]

    act = await get_activity_stats(guild_id, days=30)
    daus = act.get('dau_data', [])
    dau_labels = act.get('dau_labels', [])
    avg_dau = act.get('avg_dau', 0)

    dau_n = len(daus)
    if dau_n > 1:
        dau_x = list(range(dau_n))
        dau_sum_x = sum(dau_x)
        dau_sum_y = sum(daus)
        dau_sum_xy = sum(i*j for i, j in zip(dau_x, daus))
        dau_sum_xx = sum(i*i for i in dau_x)
        try:
            dau_slope = (dau_n*dau_sum_xy - dau_sum_x*dau_sum_y) / (dau_n*dau_sum_xx - dau_sum_x**2)
            dau_intercept = (dau_sum_y - dau_slope*dau_sum_x) / dau_n
        except:
            dau_slope = 0
            dau_intercept = avg_dau
    else:
        dau_slope = 0
        dau_intercept = avg_dau

    dau_weekday_totals = [0] * 7
    dau_weekday_counts = [0] * 7
    for i, val in enumerate(daus):
        if i < len(hist_dates):
            wd = hist_dates[i].weekday()
            dau_weekday_totals[wd] += val
            dau_weekday_counts[wd] += 1

    dau_global_avg = sum(daus) / dau_n if dau_n > 0 else 1
    if dau_global_avg == 0: dau_global_avg = 1

    dau_seasonality = []
    for d in range(7):
        avg_for_day = dau_weekday_totals[d] / dau_weekday_counts[d] if dau_weekday_counts[d] > 0 else dau_global_avg
        dau_seasonality.append(avg_for_day / dau_global_avg)

    dau_forecast = []
    dau_forecast_labels = []
    for i in range(1, 8):
        future_x = (dau_n - 1) + i
        trend_level = dau_slope * future_x + dau_intercept
        if trend_level < 0: trend_level = 0

        future_wd = (today_weekday + i) % 7
        seasonal_adjust = dau_seasonality[future_wd] if future_wd < len(dau_seasonality) else 1

        final_dau = round(trend_level * seasonal_adjust)
        dau_forecast.append(final_dau)

        future_date = end_dt + datetime.timedelta(days=i)
        dau_forecast_labels.append(future_date.strftime("%Y-%m-%d"))

    expected_dau = dau_forecast[0] if dau_forecast else round(avg_dau)

    mau_key = f"hll:mau:{guild_id}:{end_dt.strftime('%Y%m')}"
    mau = await r.pfcount(mau_key)
    mau_available = mau > 0
    # BP principle: missing data != zero. Do not fabricate MAU from DAU.

    dau_mau_ratio = round((avg_dau / mau * 100), 1) if mau > 0 else None

    mau_growth_rate = 1.0 + (avg_monthly_growth / max(1, current_members)) if avg_monthly_growth > 0 else 1.0
    mau_forecast = [mau]
    for i in range(1, 4):
        mau_forecast.append(round(mau_forecast[-1] * mau_growth_rate))

    # BP principle: churn/inactivity risk comes only from Markov model.
    # Do not fabricate churn_score from leave counts — that is not a
    # predictive method described in the thesis.
    if research_data.get("success") and research_data.get("inactivity_risk_pct") is not None:
        churn_score = research_data.get("inactivity_risk_pct")
        churn_available = True
    else:
        churn_score = None
        churn_available = False

    res_dict = {
        "history": {
            "dates": history_dates,
            "members": history_members,
            "joins": joins_history[-12:] if len(joins_history) > 12 else joins_history,
            "leaves": leaves_history[-12:] if len(leaves_history) > 12 else leaves_history
        },
        "forecast": {
            "dates": forecast_dates,
            "members": forecast_members,
            "days": forecast_day_labels,
            "activity": forecast_activity
        },
        "dau": {
            "history": daus,
            "history_labels": dau_labels,
            "forecast": dau_forecast,
            "forecast_labels": dau_forecast_labels,
            "avg": round(avg_dau),
            "trend": "up" if dau_slope > 0 else "down" if dau_slope < 0 else "stable"
        },
        "mau": {
            "current": mau if mau_available else None,
            "available": mau_available,
            "reason": None if mau_available else "missing_mau_data",
            "forecast": mau_forecast if mau_available else [],
            "dau_mau_ratio": dau_mau_ratio
        },
        "predictions": {
            "available": len(activity_history) >= 7,
            "reason": None if len(activity_history) >= 7 else "insufficient_history",
            "members_30d": predicted_members_30d,
            "members_growth_pct": growth_pct,
            "expected_msgs_tomorrow": expected_msgs_tomorrow,
            "expected_dau": expected_dau,
            "avg_dau": round(avg_dau),
            "churn_risk": churn_score,
            "churn_available": churn_available,
            "avg_monthly_growth": round(avg_monthly_growth, 1),
            "current_members": current_members,
            "method": "average_monthly_net_growth",
            "experimental": True,
            "validated_prediction": False
        },
        "channels": []
    }

    try:
        from ..utils import get_channel_distribution

        dist = await get_channel_distribution(int(guild_id), days=30)

        channels_info = await get_discord_channels(int(guild_id))
        cmap = {str(c['id']): c['name'] for c in channels_info}

        predicted_channels = []
        total_baseline = sum(c['count'] for c in dist) if dist else 1

        for d in dist[:5]:
            share = d['count'] / total_baseline
            pred_count = round(share * expected_msgs_tomorrow)
            predicted_channels.append({
                "name": cmap.get(str(d['channel_id']), f"#{d['channel_id']}"),
                "count": pred_count
            })

        res_dict["channels"] = predicted_channels
        return JSONResponse(res_dict)

    except Exception as e:
        print(f"Error in channel predictions: {e}")
        return JSONResponse(res_dict)

@router.post("/api/delete-server-data")
async def delete_server_data(request: Request, _=Depends(require_admin)):
    """Delete all Redis data for the current server (Admin only)."""
    try:
        await require_csrf(request)
    except HTTPException:
        return JSONResponse({"status": "error", "message": "Neplatný CSRF token"}, status_code=403)

    guild_id = request.session.get("guild_id")
    if not guild_id:
        return JSONResponse({"status": "error", "message": "No guild selected"}, status_code=400)

    if guild_id == "demo-guild":
        return JSONResponse({"status": "error", "message": "Přístup odepřen: Akce není v demo režimu povolena."}, status_code=403)

    from ..utils import get_redis_client
    r = await get_redis_client()

    patterns = [
        f"stats:*:{guild_id}*",
        f"hll:*:{guild_id}*",
        f"events:*:{guild_id}*",
        f"backfill:*:{guild_id}*",
        f"user:*:{guild_id}*",
        f"daily:*:{guild_id}*",
    ]

    deleted_count = 0
    for pattern in patterns:
        keys = []
        async for key in r.scan_iter(pattern):
            keys.append(key)
        if keys:
            deleted_count += await r.delete(*keys)

    await r.srem("bot:guilds", guild_id)

    return JSONResponse({
        "status": "ok",
        "message": f"Smazáno {deleted_count} klíčů pro server {guild_id}"
    })

@router.post("/api/trigger-backfill")
async def trigger_backfill(request: Request, _=Depends(require_admin)):
    """Trigger backfill process."""
    try:
        await require_csrf(request)
    except HTTPException:
        return JSONResponse({"status": "error", "message": "Neplatný CSRF token"}, status_code=403)

    guild_id = request.session.get("guild_id")
    if not guild_id:
        return JSONResponse({"status": "error", "message": "No guild selected"}, status_code=400)

    if guild_id == "demo-guild":
        return JSONResponse({"status": "error", "message": "Tato akce není v demu povolena."}, status_code=403)

    from ..utils import get_redis_client
    r = await get_redis_client()

    await r.hset(f"backfill:status:{guild_id}", mapping={
        "status": "processing",
        "total_messages": 0,
        "current_channel": "inicializace"
    })

    import subprocess
    import sys
    import os

    is_discourse = False
    try:
        is_discourse = int(guild_id) < 0
    except ValueError:
        pass

    if is_discourse:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "discourse_sync.py"))
        cmd = [sys.executable, script_path, "--guild_id", str(guild_id), "--backfill"]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "backfill_stats.py"))

        # Extract bot token from config or .env
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            try:
                from ....config.dashboard_secrets import BOT_TOKEN
                bot_token = BOT_TOKEN
            except:
                pass

        if bot_token:
            # User requested complete history (set days to 10 years to cover everything)
            cmd = [sys.executable, script_path, "--guild_id", str(guild_id), "--days", "3650"]
            env = {**os.environ, "BOT_TOKEN": bot_token}
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        else:
            await r.hset(f"backfill:status:{guild_id}", mapping={
                "status": "error",
                "message": "Bot token not found"
            })

    return JSONResponse({"status": "ok", "message": "Backfill spuštěn."})

@router.get("/api/backfill-status")
async def backfill_status(request: Request, _=Depends(require_admin)):
    """Get backfill status."""
    guild_id = request.session.get("guild_id")
    if not guild_id:
        return JSONResponse({"status": "error", "message": "No guild selected"}, status_code=400)

    from ..utils import get_redis_client
    r = await get_redis_client()
    status = await r.hgetall(f"backfill:status:{guild_id}")

    if not status:
        return JSONResponse({"status": "none"})

    return JSONResponse({
        "status": status.get("status", "error"),
        "total_messages": int(status.get("total_messages", 0)),
        "current_channel": status.get("current_channel", ""),
        "message": status.get("message", "Neznámá chyba")
    })

@router.post("/api/leave-server")
async def leave_server(request: Request, _=Depends(require_admin)):
    """Remove bot from current server (Admin only)."""
    try:
        await require_csrf(request)
    except HTTPException:
        return JSONResponse({"status": "error", "message": "Neplatný CSRF token"}, status_code=403)

    guild_id = request.session.get("guild_id")
    if not guild_id:
        return JSONResponse({"status": "error", "message": "No guild selected"}, status_code=400)

    if guild_id == "demo-guild":
        return JSONResponse({"status": "error", "message": "Přístup odepřen: Akce není v demo režimu povolena."}, status_code=403)

    import httpx
    import os

    token_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "bot_token.py"))
    primary_token = None
    dashboard_token = None
    if os.path.exists(token_path):
        with open(token_path, 'r') as f:
            for line in f:
                if line.strip().startswith("TOKEN ="):
                    primary_token = line.split("=")[1].strip().strip('"').strip("'")
                elif line.strip().startswith("DASHBOARD_TOKEN ="):
                    dashboard_token = line.split("=")[1].strip().strip('"').strip("'")

    from ..utils import get_redis_client
    r = await get_redis_client()
    primary_guilds = await r.smembers("bot:guilds:primary") or set()
    dashboard_guilds = await r.smembers("bot:guilds:dashboard") or set()

    if guild_id in primary_guilds:
        bot_token = primary_token
    elif guild_id in dashboard_guilds:
        bot_token = dashboard_token
    else:
        bot_token = dashboard_token or primary_token

    if not bot_token:
        return JSONResponse({"status": "error", "message": "Bot token not found"}, status_code=500)

    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"https://discord.com/api/v10/users/@me/guilds/{guild_id}",
            headers={"Authorization": f"Bot {bot_token}"}
        )

        if resp.status_code == 204:

            await r.srem("bot:guilds", guild_id)

            request.session.pop("guild_id", None)
            request.session.pop("guild_name", None)
            return JSONResponse({"status": "ok", "message": "Bot byl odebrán ze serveru"})
        else:
            return JSONResponse({
                "status": "error",
                "message": f"Discord API error: {resp.status_code}"
            }, status_code=500)

@router.get("/api/analytics-tools")
async def get_analytics_tools(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None, _=Depends(require_auth)):
    """Get data for analytical tools."""
    try:
        guild_id = get_guild_id(request)

        if guild_id == "demo-guild":
            s = get_demo_stats(start_date, end_date)
            return JSONResponse({
                "status": "ok",
                "trends": s["trends"],
                "engagement": s["engagement"],
                "insights": s["insights"],
                "dqs": {
                    "score": 95,
                    "is_sufficient": True,
                    "history_days": 120,
                    "total_events": 15420,
                    "reasons": ["Není připojeno fórum Discourse (zobrazují se pouze data z Discordu)."]
                }
            })
    except Exception as e:
        print(f"Error in analytics-tools initial check: {e}")

    from ..utils import get_trend_analysis, get_engagement_score, get_insights
    from ..services.analytics_service import DefaultAnalyticsService
    from ..repositories.redis_repo import RedisRepository

    try:
        trends = await get_trend_analysis(guild_id)
        engagement = await get_engagement_score(guild_id, start_date=start_date, end_date=end_date)
        insights = await get_insights(guild_id)

        repo = RedisRepository()
        service = DefaultAnalyticsService(repo)
        dqs = await service.get_data_quality_score(int(guild_id)) if str(guild_id).isdigit() else None

        # Add retention to engagement payload
        member_stats = await load_member_stats(guild_id, start_date=start_date, end_date=end_date)
        engagement["retention"] = member_stats.get("retention_rate", 0.0) if member_stats else 0.0

        return JSONResponse({
            "status": "ok",
            "trends": trends,
            "engagement": engagement,
            "insights": insights,
            "dqs": dqs
        })
    except Exception as e:
         return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@router.get("/api/extended-stats")
async def get_extended_stats(request: Request, start_date: str = None, end_date: str = None, _=Depends(require_auth)):
    """Get extended statistics for new widgets."""
    guild_id = request.session.get("guild_id")
    if not guild_id: return JSONResponse({"status": "error"}, status_code=400)

    if guild_id == "demo-guild":
        s = get_demo_stats()
        return JSONResponse({
            "status": "ok",
            "hourly_dist": s["redis_stats"]["hourly_activity"],
            "weekly_dist": s["deep_stats"]["weekly_data"],
            "msg_length_dist": s["redis_stats"]["msglen_data"],
            "avg_msg_len": s["deep_stats"]["avg_msg_len"],
            "dates": s["labels"],
            "growth_total": s["total_data"],
            "joins": s["joins_data"],
            "leaves": s["leaves_data"],
            "weekend_ratio": {"weekday": 750, "weekend": 250},
            "stickiness": s["deep_stats"]["dau_mau_ratio"]
        })

    guild_id = int(guild_id)

    print(f"[EXTENDED STATS] Request for guild: {guild_id}")

    from ..utils import get_deep_stats_redis, get_redis_dashboard_stats, load_member_stats

    try:

        deep = await get_deep_stats_redis(guild_id, start_date=start_date, end_date=end_date)
        dash = await get_redis_dashboard_stats(guild_id, start_date=start_date, end_date=end_date)
        growth = await load_member_stats(guild_id, start_date=start_date, end_date=end_date)

        heatmap = dash.get('heatmap_data', [])
        hourly_dist = [0] * 24
        if heatmap:
            for d in range(7):
                for h in range(24):
                    try: hourly_dist[h] += heatmap[d][h]
                    except: pass

        weekly = deep.get('weekly_data', [0]*7)
        weekday_sum = sum(weekly[0:5])
        weekend_sum = sum(weekly[5:7])

        return JSONResponse({
            "status": "ok",
            "hourly_dist": hourly_dist,
            "weekly_dist": weekly,
            "msg_length_dist": deep.get('msglen_data', [0]*5),
            "avg_msg_len": deep.get('avg_msg_len', 0),
            "dates": growth.get('labels', []),
            "growth_total": growth.get('total', []),
            "joins": growth.get('joins', []),
            "leaves": growth.get('leaves', []),
            "weekend_ratio": {"weekday": weekday_sum, "weekend": weekend_sum},
            "stickiness": deep.get('dau_mau_ratio', [])
        })
    except Exception as e:
        print(f"Extended stats error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@router.get("/api/export/{export_type}")
async def export_data(
    export_type: str,
    request: Request,
    format: str = "json",
    start_date: str = None,
    end_date: str = None,
    _=Depends(require_auth),
    __=Depends(require_export_data),
):
    """Export selected community analytics as bounded CSV or JSON."""
    import csv
    import io
    import json
    import time
    from datetime import datetime as dt, timedelta as td

    allowed_types = {
        "leaderboard", "voice_top", "commands_top", "emojis_top",
        "channels", "channels_top", "channels_full", "activity",
        "users", "traffic", "hourly_heatmap", "msg_lengths",
    }
    if export_type not in allowed_types:
        return JSONResponse({"error": "Unsupported export type"}, status_code=400)

    output_format = format.lower()
    if output_format not in {"csv", "json"}:
        return JSONResponse({"error": "Format must be 'csv' or 'json'"}, status_code=400)

    guild_id = request.session.get("guild_id")
    if not guild_id:
        return JSONResponse({"error": "No guild selected"}, status_code=400)
    if guild_id == "demo-guild":
        return JSONResponse({"error": "Export is not available in demo mode."}, status_code=403)

    try:
        period_end = dt.strptime(end_date, "%Y-%m-%d") if end_date else dt.now()
        period_start = dt.strptime(start_date, "%Y-%m-%d") if start_date else period_end - td(days=6)
    except ValueError:
        return JSONResponse({"error": "Dates must use YYYY-MM-DD"}, status_code=400)
    if period_start > period_end:
        return JSONResponse({"error": "start_date must not be after end_date"}, status_code=400)
    if (period_end.date() - period_start.date()).days + 1 > 365:
        return JSONResponse({"error": "Export range is limited to 365 days"}, status_code=400)

    from ..utils import get_redis_client, get_activity_stats, get_leaderboard_data, get_channel_distribution

    try:
        r = await get_redis_client()
        user_id = request.session.get("discord_user", {}).get("id", "anonymous")
        bucket = int(time.time() // 60)
        rate_key = f"export:rate:{guild_id}:{user_id}:{bucket}"
        request_count = await r.incr(rate_key)
        if request_count == 1:
            await r.expire(rate_key, 120)
        if request_count > 120:
            return JSONResponse({"error": "Export rate limit exceeded"}, status_code=429)

        headers = []
        data_rows = []

        if export_type == "leaderboard":
            headers = ["user_id", "name", "total_messages", "avg_length_chars"]
            lb_data = await get_leaderboard_data(
                guild_id, limit=1000,
                start_date=period_start.strftime("%Y-%m-%d"),
                end_date=period_end.strftime("%Y-%m-%d"),
            )
            data_rows = [
                [u["user_id"], u["name"], u["total_messages"], u["avg_message_length"]]
                for u in lb_data.get("leaderboard", [])
            ]

        elif export_type == "voice_top":
            headers = ["user_id", "name", "total_seconds", "hours", "minutes"]
            voice_lb = await r.zrevrange(f"stats:voice_duration:{guild_id}", 0, -1, withscores=True)
            pipe = r.pipeline()
            for uid, _score in voice_lb:
                pipe.hget(f"user:info:{uid}", "name")
            names = await pipe.execute()
            for index, (uid, duration) in enumerate(voice_lb):
                seconds = int(duration)
                data_rows.append([uid, names[index] or f"User {uid}", seconds, seconds // 3600, (seconds % 3600) // 60])

        elif export_type == "commands_top":
            headers = ["command", "usage_count"]
            commands = await r.hgetall(f"stats:commands:{guild_id}")
            data_rows = [[name, int(count)] for name, count in sorted(commands.items(), key=lambda item: int(item[1]), reverse=True)]

        elif export_type == "emojis_top":
            headers = ["emoji", "usage_count", "type"]
            emojis = await r.zrevrange(f"stats:emojis:{guild_id}", 0, -1, withscores=True)
            data_rows = [[emoji, int(count), "Custom" if len(str(emoji)) > 8 else "Unicode"] for emoji, count in emojis]

        elif export_type in {"channels", "channels_top", "channels_full"}:
            headers = ["channel_id", "name", "message_count"]
            channels = await get_channel_distribution(
                guild_id,
                start_date=period_start.strftime("%Y-%m-%d"),
                end_date=period_end.strftime("%Y-%m-%d"),
            )
            pipe = r.pipeline()
            for channel in channels:
                pipe.hget(f"channel:info:{channel['channel_id']}", "name")
            names = await pipe.execute()
            data_rows = [
                [channel["channel_id"], names[index] or f"Channel {channel['channel_id']}", channel["count"]]
                for index, channel in enumerate(channels)
            ]

        elif export_type == "activity":
            headers = ["date", "messages", "voice_minutes", "joins", "leaves", "dau"]
            dates = []
            current = period_start
            while current.date() <= period_end.date():
                dates.append(current)
                current += td(days=1)

            voice_by_day = {day.strftime("%Y-%m-%d"): 0 for day in dates}
            range_start = period_start.replace(hour=0, minute=0, second=0).timestamp()
            range_end = period_end.replace(hour=23, minute=59, second=59).timestamp()
            async for key in r.scan_iter(f"events:voice:{guild_id}:*"):
                for raw, score in await r.zrangebyscore(key, range_start, range_end, withscores=True):
                    try:
                        day_key = dt.fromtimestamp(float(score)).strftime("%Y-%m-%d")
                        voice_by_day[day_key] = voice_by_day.get(day_key, 0) + int(json.loads(raw).get("duration", 0))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue

            joins = await r.hgetall(f"stats:joins:daily:{guild_id}")
            leaves = await r.hgetall(f"stats:leaves:daily:{guild_id}")
            pipe = r.pipeline()
            for day in dates:
                compact = day.strftime("%Y%m%d")
                pipe.hgetall(f"stats:hourly:{guild_id}:{compact}")
                pipe.pfcount(f"hll:dau:{guild_id}:{compact}")
            values = await pipe.execute()
            for index, day in enumerate(dates):
                label = day.strftime("%Y-%m-%d")
                hourly = values[index * 2] or {}
                messages = sum(int(value) for value in hourly.values())
                dau = int(values[index * 2 + 1])
                data_rows.append([
                    label, messages, round(voice_by_day.get(label, 0) / 60, 2),
                    int(joins.get(label, 0)), int(leaves.get(label, 0)), dau,
                ])

        elif export_type == "users":
            headers = ["user_id", "name", "total_messages", "joined_at", "roles"]
            lb_data = await get_leaderboard_data(
                guild_id, limit=1000,
                start_date=period_start.strftime("%Y-%m-%d"),
                end_date=period_end.strftime("%Y-%m-%d"),
            )
            active_users = lb_data.get("leaderboard", [])
            pipe = r.pipeline()
            for user in active_users:
                pipe.hgetall(f"user:info:{user['user_id']}")
            infos = await pipe.execute()
            data_rows = [
                [user["user_id"], user["name"], user["total_messages"], (infos[index] or {}).get("joined_at", ""), (infos[index] or {}).get("roles", "")]
                for index, user in enumerate(active_users)
            ]

        elif export_type == "traffic":
            from ..utils import load_member_stats
            headers = ["date", "joins", "leaves", "total_members"]
            stats = await load_member_stats(
                guild_id,
                start_date=period_start.strftime("%Y-%m-%d"),
                end_date=period_end.strftime("%Y-%m-%d"),
            )
            labels, joins, leaves, totals = stats.get("labels", []), stats.get("joins", []), stats.get("leaves", []), stats.get("total", [])
            data_rows = [[label, joins[index], leaves[index], totals[index]] for index, label in enumerate(labels)]

        elif export_type == "hourly_heatmap":
            headers = ["day_hour", "message_count"]
            heatmap = await r.hgetall(f"stats:heatmap:{guild_id}")
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for key in sorted(heatmap):
                try:
                    day_index, hour = (int(value) for value in key.split("_", 1))
                    day_name = day_names[day_index] if 0 <= day_index <= 6 else str(day_index)
                    data_rows.append([f"{day_name} {hour:02d}:00", int(heatmap[key])])
                except (ValueError, TypeError):
                    continue

        elif export_type == "msg_lengths":
            headers = ["length_range", "count"]
            raw_buckets = await r.zrange(f"stats:msglen:{guild_id}", 0, -1, withscores=True)
            labels = {0: "0 chars", 5: "1-10 chars", 30: "11-50 chars", 75: "51-100 chars", 150: "101-200 chars", 250: "201+ chars"}
            data_rows = [[labels.get(int(float(bucket)), str(bucket)), int(score)] for bucket, score in raw_buckets]

        generated_at = dt.now().isoformat()
        period = {"start": period_start.strftime("%Y-%m-%d"), "end": period_end.strftime("%Y-%m-%d")}
        timestamp = dt.now().strftime("%Y%m%d_%H%M")
        filename = f"{export_type}_{guild_id}_{timestamp}"

        if output_format == "json":
            if export_type == "activity":
                payload = {
                    "guild_id": str(guild_id), "period": period,
                    "generated_at": generated_at,
                    "daily": [dict(zip(headers, row)) for row in data_rows],
                }
            else:
                payload = {
                    "export_type": export_type, "guild_id": str(guild_id),
                    "period": period, "generated_at": generated_at,
                    "count": len(data_rows),
                    "data": [dict(zip(headers, row)) for row in data_rows],
                }
            return JSONResponse(
                payload,
                headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
            )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data_rows)
        return Response(
            content=output.getvalue(), media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )
    except Exception as exc:
        print(f"Export error: {exc}")
        return JSONResponse({"error": "Export generation failed"}, status_code=500)

@router.get("/api/logs")
async def get_live_logs(request: Request, _=Depends(require_admin)):
    """API endpoint to get live logs from Redis."""
    guild_id = request.session.get("guild_id")
    if guild_id == "demo-guild":
        return {"logs": get_demo_logs()}

    try:
        r = await get_redis_client()
        logs = await r.lrange("dashboard:live_logs", 0, -1)
        return {"logs": logs[::-1]}
    except Exception as e:
        return {"logs": [f"Error fetching logs: {e}"]}

@router.get("/api/peak-stats")
async def get_peak_stats_api(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None, role_id: str = "all", _=Depends(require_view_stats)):
    """Get peak activity stats."""
    guild_id = get_guild_id(request)

    if guild_id == "demo-guild":
        return {
            "peak_hour": "21:00",
            "peak_day": "Sobota",
            "peak_messages": 1240,
            "quiet_period": "03:00 - 05:00"
        }

    redis_stats = await get_redis_dashboard_stats(int(guild_id), start_date=start_date, end_date=end_date, role_id=role_id)
    return {
        "peak_hour": redis_stats.get("peak_hour", "--"),
        "peak_day": redis_stats.get("peak_day", "--"),
        "peak_messages": redis_stats.get("peak_messages", "--"),
        "quiet_period": redis_stats.get("quiet_period", "--")
    }

@router.get("/api/channel-stats")
async def get_channel_stats(request: Request, start_date=None, end_date=None, role_id="all", platform: str = "all", channel_id: str = None, _=Depends(require_view_stats)):
    """Get per-channel activity statistics."""
    try:
        gid = request.session.get("guild_id")
        if gid == "demo-guild":
            return {
                "channels": [
                    {"name": "obecné", "count": 14502},
                    {"name": "hry", "count": 8230},
                    {"name": "pokec", "count": 12400},
                    {"name": "bot-spam", "count": 3100},
                    {"name": "oznámení", "count": 120}
                ], "guild_id": gid
            }
        gid = get_guild_id(request)
        if platform != "all" or channel_id:
            from ..services.analytics_service import DefaultAnalyticsService
            from ..repositories.redis_repo import RedisRepository
            topic_id = channel_id if platform == "discourse" else None
            discord_channel_id = None if platform == "discourse" else channel_id
            rows = await DefaultAnalyticsService(RedisRepository()).get_channel_activity(
                int(gid), start_date, end_date, platform, discord_channel_id, topic_id
            )
            r = await get_redis_client()
            for row in rows:
                item_id = row["channel_id"]
                if row.get("platform") == "discourse":
                    row["name"] = f"Téma {item_id}"
                else:
                    row["name"] = await r.hget(f"channel:info:{item_id}", "name") or f"#{item_id}"
                row["count"] = row.pop("messages")
            return {"channels": rows, "guild_id": gid, "platform": platform}

        dist = await get_channel_distribution(gid, start_date=start_date, end_date=end_date)

        channels = await get_discord_channels(gid)
        cmap = {str(c['id']): c['name'] for c in channels}

        for d in dist:
            d['name'] = cmap.get(str(d['channel_id']), f"#{d['channel_id']}")

        return {"channels": dist, "guild_id": gid}
    except Exception as e:
        return {"error": str(e), "channels": [], "guild_id": None}

@router.get("/api/leaderboard")
async def api_leaderboard(request: Request, limit: int = 15, start_date=None, end_date=None, role_id="all", _=Depends(require_view_stats)):
    """Get user leaderboard."""
    try:
        gid = get_guild_id(request)
        if gid == "demo-guild":
            from ..demo_data import get_demo_stats
            stats = get_demo_stats()
            # Standardize 'name' vs 'username' for frontend to avoid empty rows
            lb_data = []
            for u in stats["deep_stats"]["leaderboard"]:
                lb_data.append({
                    "rank": u["rank"],
                    "name": u.get("name") or u.get("username"),
                    "total_messages": u.get("action_count", 0),
                    "avg_message_length": int(u.get("weighted_h", 0) * 10) # Mock metric
                })
            return {"leaderboard": lb_data, "guild_id": gid}
        gid = get_guild_id(request)
        data = await get_leaderboard_data(gid, limit=limit, start_date=start_date, end_date=end_date)
        data["guild_id"] = gid
        return data
    except Exception as e:
        return {"error": str(e), "leaderboard": [], "guild_id": None}

@router.get("/api/comparisons")
async def api_time_comparisons(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None, _=Depends(require_view_stats)):
    """Get WoW and MoM comparisons."""
    try:
        guild_id = request.session.get("guild_id")
        if guild_id == "demo-guild":
            # Realističtější a stabilnější hodnoty pro obhajobu
            data = {
                "week_over_week": {
                    "this_week": 24.0,
                    "change_percent": 2.4
                },
                "month_over_month": {
                    "this_month": 24.0,
                    "change_percent": 6.8
                }
            }
            print(f"DEBUG: Returning demo comparison data: {data}")
            return data

        guild_id = get_guild_id(request)
        return await get_time_comparisons(guild_id, start_date=start_date, end_date=end_date)
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/security-score")
async def api_security_score(request: Request, _=Depends(require_auth)):
    """Get security score for the current guild."""
    try:
        print("[DEBUG] /api/security-score invoked")
        guild_id = get_guild_id(request)

        if guild_id == "demo-guild":
            s = get_demo_stats()
            sec = s["security_score_data"]
            return JSONResponse({
                "overall_score": sec["overall_score"],
                "rating": sec["rating"],
                "rating_color": sec["rating_color"],
                "components": {
                    "mod_ratio": {"score": sec["mod_ratio_score"], "value": "1:72", "label": "Moderátorů"},
                    "security": {"score": sec["security_settings_score"], "value": "Medium", "label": "Zabezpečení"},
                    "engagement": {"score": sec["engagement_score"], "value": "24%", "label": "Engagement"},
                    "moderation": {"score": sec["moderation_score"], "value": "Aktivní", "label": "Moderace"}
                },
                "insights": [i["text"] for i in s["insights"]]
            })

        print(f"[DEBUG] Calculating score for guild {guild_id}")
        score_data = await get_security_score(guild_id)
        print(f"[DEBUG] Score result: {score_data}")
        return JSONResponse(score_data)
    except HTTPException as he:
        print(f"[ERROR] Security Score HTTP Error: {he.detail}")
        return JSONResponse({"error": he.detail, "overall_score": 0, "rating": "N/A", "components": {}}, status_code=he.status_code)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Security Score Exception: {e}")
        return JSONResponse({"error": str(e), "overall_score": 0, "rating": "Error", "components": {}}, status_code=500)

@router.get("/api/voice-stats")
async def api_voice_stats(
    request: Request,
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    role_id: str = "all",
    _=Depends(require_view_stats),
):
    """API endpoint for voice leaderboard."""
    gid = get_guild_id(request)
    if gid == "demo-guild":
        return {
            "leaderboard": [
                {"user_id": "demo-1", "name": "Demo User 1", "duration": 3600, "minutes": 60, "duration_fmt": "1h 0m"},
                {"user_id": "demo-2", "name": "Demo User 2", "duration": 1800, "minutes": 30, "duration_fmt": "30m"}
            ]
        }
    gid = get_guild_id(request)
    return await get_voice_leaderboard(gid, limit, start_date=start_date, end_date=end_date, role_id=role_id)

@router.get("/api/command-stats")
async def api_command_stats(
    request: Request,
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    role_id: str = "all",
    _=Depends(require_view_stats),
):
    """API endpoint for command usage stats."""
    gid = get_guild_id(request)
    if gid == "demo-guild":
        return {
            "commands": [
                {"name": "/help", "count": 150},
                {"name": "/stats", "count": 120},
                {"name": "/leaderboard", "count": 85}
            ]
        }
    gid = get_guild_id(request)
    return await get_command_stats(gid, limit, start_date=start_date, end_date=end_date, role_id=role_id)

@router.get("/api/traffic-stats")
async def api_traffic_stats(
    request: Request,
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    role_id: str = "all",
    _=Depends(require_view_stats),
):
    """API endpoint for traffic stats (joins/leaves)."""
    gid = get_guild_id(request)
    if gid == "demo-guild":
        s = get_demo_stats()
        return s["member_stats"]
    gid = get_guild_id(request)
    return await get_traffic_stats(gid, days=days, start_date=start_date, end_date=end_date, role_id=role_id)

@router.get("/api/channel-distribution")
async def api_channel_distribution(request: Request, start_date=None, end_date=None, role_id="all", _=Depends(require_view_stats)):
    """DEPRECATED: Redirecting to channel-stats."""
    gid = get_guild_id(request)
    if gid == "demo-guild":
        return {
            "channels": [
                {"channel_id": "1", "name": "obecné", "count": 14502},
                {"channel_id": "2", "name": "pokec", "count": 12400}
            ],
            "guild_id": gid
        }
    return await get_channel_stats(request, start_date, end_date, role_id)

@router.get("/api/health-research")
async def api_health_research(request: Request, _=Depends(require_view_stats)):
    """API endpoint pro výzkumná data (Markov, Survival)."""
    gid = get_guild_id(request)
    if gid == "demo-guild":
        return {
            "success": True,
            "activity_rate_pct": 14.5,
            "mii": 0.048,
            "mii_pct": 4.8,
            "rec_mods": 4,
            "retention_pct": 82.3,
            "churn_risk_pct": 14.0,
            "inactivity_risk_pct": 14.0,
            "life_expectancy_days": 42.5,
            "activity_survival_expectancy_days": 42.5,
            "median_survival_days": 29.3,
            "median_activity_survival_days": 29.3,
            "survival_curve": {
                "0": 1.0,
                "7": 0.95,
                "14": 0.88,
                "21": 0.84,
                "30": 0.81,
                "60": 0.75,
                "90": 0.68,
                "180": 0.55
            },
            "state_distribution": {
                "new": 120,
                "active": 350,
                "passive": 150,
                "inactive": 80
            },
            "predicted_distribution": {
                "new": 0.18,
                "active": 0.44,
                "passive": 0.24,
                "inactive": 0.14
            }
        }
    return await get_health_research_data(gid)

@router.get("/api/channel-activity")
async def api_channel_activity(request: Request, start_date: str = None, end_date: str = None, platform: str = "all", channel_id: str = None, topic_id: str = None, _=Depends(require_auth)):
    if platform == "discourse" and channel_id and not topic_id:
        topic_id = channel_id
        channel_id = None
    guild_id = request.session.get("guild_id")
    from ..services.analytics_service import DefaultAnalyticsService
    from ..repositories.redis_repo import RedisRepository
    repo = RedisRepository()
    service = DefaultAnalyticsService(repo)
    data = await service.get_channel_activity(int(guild_id) if guild_id else 0, start_date, end_date, platform, channel_id, topic_id)
    return {"status": "ok", "data": data}

@router.get("/api/health/support")
async def api_health_support(request: Request, days: int = 30, _=Depends(require_auth)):
    guild_id = request.session.get("guild_id")
    from ..services.analytics_service import DefaultAnalyticsService
    from ..repositories.redis_repo import RedisRepository
    repo = RedisRepository()
    service = DefaultAnalyticsService(repo)
    data = await service.get_community_health_support(int(guild_id), days)
    return {"status": "ok", "data": data}

@router.post("/api/admin/support-channels", dependencies=[Depends(require_auth), Depends(require_csrf)])
async def api_set_support_channels(request: Request):
    # Simple endpoint to configure support channels
    guild_id = request.session.get("guild_id")
    data = await request.json()
    from ..utils import get_redis
    import json
    r = await get_redis()

    cfg_str = await r.get(f"config:settings:{guild_id}")
    if cfg_str:
        cfg = json.loads(cfg_str)
    else:
        cfg = {}

    if "support_channels" in data:
        cfg["support_channels"] = data["support_channels"]
    if "support_detection_mode" in data:
        cfg["support_detection_mode"] = data["support_detection_mode"]

    await r.set(f"config:settings:{guild_id}", json.dumps(cfg))
    return {"status": "ok"}
