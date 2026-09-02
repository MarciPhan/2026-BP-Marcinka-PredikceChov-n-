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
                if key not in os.environ:
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

from shared.config import settings as app_settings

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
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_urlsafe(32)
    if not ACCESS_TOKEN:
        ACCESS_TOKEN = secrets.token_urlsafe(32)
except ImportError:
    # fallback to generated secrets for dev
    SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY") or secrets.token_urlsafe(32)
    ACCESS_TOKEN = os.getenv("DASHBOARD_ACCESS_TOKEN") or secrets.token_urlsafe(32)
    SESSION_EXPIRY_HOURS = 24
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8093/auth/callback")
    ADMIN_USER_IDS = []
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
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

# OTP email auth removed – přihlášení pouze přes Discord OAuth2 nebo Demo

app = FastAPI(
    title="CommunityMetrics API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    description="Dokumentované rozhraní pro komunitní analytiku. Endpointy /api/v1 vyžadují hlavičku X-API-Key.",
)


app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=SESSION_EXPIRY_HOURS * 3600, same_site="lax", https_only=(app_settings.environment == "production"))

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
from .routers.community_health import router as community_health_router

app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(community_health_router)







@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/img/favicon.png") 




















async def require_auth(request: Request):
    # Kontrola, jestli je uživatel přihlášen
    
    allowed_paths = ["/login", "/login/demo", "/auth/callback", "/logout"]
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


from starlette.exceptions import HTTPException as StarletteHTTPException
from .utils import get_sidebar_context

@app.exception_handler(401)
async def redirect_to_login_handler(request: Request, exc: StarletteHTTPException):
    return RedirectResponse(url="/", status_code=302)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        
    is_demo = request.session.get("role") == "demo"
    if exc.status_code == 403 and is_demo:
        referer = request.headers.get("referer")
        if referer:
            import urllib.parse
            url_parts = list(urllib.parse.urlparse(referer))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query["error"] = "demo_restricted"
            url_parts[4] = urllib.parse.urlencode(query)
            return RedirectResponse(url=urllib.parse.urlunparse(url_parts), status_code=303)
        return RedirectResponse(url="/?error=demo_restricted", status_code=303)

    titles = {
        400: "Špatný požadavek",
        403: "Přístup odepřen",
        404: "Stránka nenalezena",
        405: "Nepovolená metoda",
        500: "Interní chyba serveru"
    }
    title = titles.get(exc.status_code, "Chyba")
    
    context = {
        "request": request,
        "status_code": exc.status_code,
        "error_title": title,
        "error_message": exc.detail
    }
    try:
        sidebar_ctx = await get_sidebar_context(request)
        context.update(sidebar_ctx)
    except Exception:
        pass
        
    return templates.TemplateResponse("error.html", context, status_code=exc.status_code)

@app.exception_handler(Exception)
async def custom_general_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"detail": "Interní chyba serveru"})
        
    context = {
        "request": request,
        "status_code": 500,
        "error_title": "Něco se pokazilo",
        "error_message": "Omlouváme se, na serveru došlo k neočekávané chybě. Tým byl upozorněn."
    }
    try:
        sidebar_ctx = await get_sidebar_context(request)
        context.update(sidebar_ctx)
    except Exception:
        pass
        
    return templates.TemplateResponse("error.html", context, status_code=500)























    
    
    









    

























if __name__ == "__main__":
    uvicorn.run("web.backend.main:app", host="0.0.0.0", port=app_settings.web_port, reload=True)



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










