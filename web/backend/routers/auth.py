from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
import urllib.parse
import httpx
import base64
import os
import secrets

# OTP email auth removed – přihlášení pouze přes Discord OAuth2 nebo Demo

# Nastavení šablon
templates = Jinja2Templates(directory="web/frontend/templates")

# Discord konfigurace
try:
    from config.dashboard_secrets import (
        DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI, ADMIN_USER_IDS
    )
except ImportError:
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8093/auth/callback")
    ADMIN_USER_IDS = []

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_BASE = "https://discord.com/api/v10"
VITE_DOCS_URL = os.environ.get("VITE_DOCS_URL", "http://localhost:5173")

router = APIRouter(tags=["auth"])

@router.get("/login/demo")
async def demo_login(request: Request):
    """Přihlášení pro demo verzi."""
    request.session["authenticated"] = True
    request.session["discord_user"] = {
        "id": "demo",
        "username": "Demo User",
        "discriminator": "0000",
        "avatar": None
    }
    request.session["guild_id"] = "demo-guild"
    request.session["guild_name"] = "Demo Server"
    request.session["role"] = "demo"
    request.session["login_time"] = datetime.now().isoformat()
    return RedirectResponse(url="/", status_code=303)



def get_effective_redirect_uri(request: Request = None) -> str:
    uri = os.getenv("DISCORD_REDIRECT_URI", "").strip()
    if uri:
        return uri
    port = os.getenv("DASHBOARD_PORT", "8092").strip()
    return f"http://localhost:{port}/auth/callback"

@router.get("/login")
async def login_page(request: Request):
    """Přesměrování na Discord OAuth."""
    client_id = os.getenv("DISCORD_CLIENT_ID", DISCORD_CLIENT_ID).strip()
    if not client_id or client_id == "YOUR_CLIENT_ID_HERE":
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Discord OAuth není nakonfigurován (chybí DISCORD_CLIENT_ID v .env). Kontaktujte administrátora."
        })
    
    redirect_uri = get_effective_redirect_uri(request)
    
    # Blbovzdornost: Pokud uživatel přistoupil přes 127.0.0.1 nebo jiný port než redirect_uri,
    # přesměrujeme na správný host/port, aby session cookie fungovala spolehlivě
    try:
        parsed_target = urllib.parse.urlparse(redirect_uri)
        req_host = request.url.hostname
        req_port = request.url.port
        if parsed_target.hostname in ("localhost", "127.0.0.1") and req_host in ("localhost", "127.0.0.1"):
            if req_host != parsed_target.hostname or (parsed_target.port and req_port != parsed_target.port):
                return RedirectResponse(url=f"{parsed_target.scheme}://{parsed_target.netloc}/login")
    except Exception:
        pass

    state_str = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state_str
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state_str
    }
    auth_url = f"{DISCORD_AUTH_URL}?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url)

@router.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, error: str = None, state: str = None):
    """Zpracování návratu z Discord OAuth."""
    if error:
        err_msg = f"Discord vrátil chybu: {error}"
        if error == "access_denied":
            err_msg = "Přihlášení přes Discord bylo zrušeno."
        return templates.TemplateResponse("login.html", {"request": request, "error": err_msg})
    if not code:
        return RedirectResponse(url="/login")
        
    saved_state = request.session.get("oauth_state")
    if "oauth_state" in request.session:
        del request.session["oauth_state"]
        
    if not state or not saved_state or not secrets.compare_digest(str(state), str(saved_state)):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Platnost přihlašovací relace vypršela nebo nastala chyba stavu (CSRF token). Zkuste se přihlásit znovu."
        })
    
    redirect_uri = get_effective_redirect_uri(request)
    client_id = os.getenv("DISCORD_CLIENT_ID", DISCORD_CLIENT_ID).strip()
    client_secret = os.getenv("DISCORD_CLIENT_SECRET", DISCORD_CLIENT_SECRET).strip()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(DISCORD_TOKEN_URL, data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            })
            
            if token_resp.status_code != 200:
                err_detail = "Ověření s Discordem selhalo."
                try:
                    err_json = token_resp.json()
                    desc = err_json.get("error_description") or err_json.get("error") or err_json.get("message")
                    if desc:
                        err_detail += f" ({desc})"
                except Exception:
                    err_detail += f" (HTTP {token_resp.status_code})"
                return templates.TemplateResponse("login.html", {"request": request, "error": err_detail})
            
            token_data = token_resp.json()
            access_token = token_data["access_token"]
            
            headers = {"Authorization": f"Bearer {access_token}"}
            user_resp = await client.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
            user_data = user_resp.json()
            
            guilds_resp = await client.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
            guilds_data = guilds_resp.json() if guilds_resp.status_code == 200 else []
        
        user_id = int(user_data["id"])
        is_admin = user_id in ADMIN_USER_IDS
        
        managed_guilds = []
        for g in guilds_data:
            perms = int(g.get("permissions", 0))
            is_admin_perm = bool(perms & 0x8)
            is_manage_guild = bool(perms & 0x20)
            is_owner = g.get("owner", False)
            
            if is_admin_perm or is_manage_guild or is_owner:
                managed_guilds.append({
                    "id": g["id"], 
                    "name": g["name"], 
                    "icon": g.get("icon"),
                    "is_admin": is_admin_perm or is_owner, 
                    "is_mod_candidate": is_manage_guild 
                })
        
        from ..utils import save_user_guilds
        await save_user_guilds(str(user_id), managed_guilds)
        
        request.session["authenticated"] = True
        request.session["discord_user"] = {
            "id": str(user_id),
            "username": user_data.get("username"),
            "discriminator": user_data.get("discriminator"),
            "avatar": user_data.get("avatar")
        }
        request.session["role"] = "admin" if is_admin else "user"
        request.session["login_time"] = datetime.now().isoformat()
        request.session["guilds_count"] = len(managed_guilds)
        
        return RedirectResponse(url="/select-server", status_code=303)
        
    except httpx.RequestError as exc:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Chyba sítě při komunikaci s Discordem."})
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Interní chyba při přihlášení: {str(exc)}"})

@router.get("/logout")
async def logout(request: Request):
    """Odhlášení a vyčištění session."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@router.get("/debug/session")
async def debug_session(request: Request):
    """Debugovací zobrazení obsahu session."""
    return {
        "session_keys": list(request.session.keys()),
        "auth": request.session.get("authenticated"),
        "role": request.session.get("role"),
        "user_id": request.session.get("discord_user", {}).get("id")
    }
