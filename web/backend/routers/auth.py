from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
import urllib.parse
import httpx
import base64
import os

from ..otp_utils import (
    validate_email, get_user_role, generate_otp, store_otp, 
    verify_otp, check_rate_limit, send_otp_email, mask_email
)

# Nastavení šablon
templates = Jinja2Templates(directory="web/frontend/templates")

# Discord konfigurace
try:
    from config.dashboard_secrets import (
        DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI, ADMIN_USER_IDS
    )
except ImportError:
    DISCORD_CLIENT_ID = ""
    DISCORD_CLIENT_SECRET = ""
    DISCORD_REDIRECT_URI = "http://localhost:8093/auth/callback"
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

@router.get("/login-email", response_class=HTMLResponse)
async def login_email_page(request: Request, error: Optional[str] = None):
    """Zobrazení stránky pro zadání emailu (OTP)."""
    return templates.TemplateResponse("login_email.html", {"request": request, "error": error})

@router.post("/api/auth/request-otp")
async def request_otp(request: Request, email: str = Form(...)):
    """Validace a odeslání OTP na e-mail."""
    is_valid, msg = validate_email(email)
    if not is_valid:
        return templates.TemplateResponse("login_email.html", {"request": request, "error": msg})
    
    allowed, wait_time = await check_rate_limit(email)
    if not allowed:
        return templates.TemplateResponse("login_email.html", {"request": request, "error": f"Příliš mnoho žádostí. Zkuste to za {wait_time} sekund."})
    
    otp = generate_otp()
    if await store_otp(email, otp):
        if await send_otp_email(email, otp):
            return RedirectResponse(url=f"/verify-otp?email={email}", status_code=303)
        else:
            return templates.TemplateResponse("login_email.html", {"request": request, "error": "Chyba při odesílání e-mailu."})
    else:
        return templates.TemplateResponse("login_email.html", {"request": request, "error": "Chyba databáze při ukládání kódu."})

@router.get("/verify-otp", response_class=HTMLResponse)
async def verify_otp_page(request: Request, email: str, error: Optional[str] = None):
    """Zobrazení stránky pro zadání OTP kódu."""
    masked = mask_email(email)
    return templates.TemplateResponse("verify_otp_page.html", {
        "request": request, 
        "email": email, 
        "masked_email": masked, 
        "error": error
    })

@router.post("/api/auth/verify-otp")
async def process_verify_otp(request: Request, email: str = Form(...), otp: str = Form(...)):
    """Ověření OTP kódu a přihlášení."""
    is_valid, msg = await verify_otp(email, otp)
    if is_valid:
        request.session["authenticated"] = True
        request.session["discord_user"] = {
            "id": f"email:{email}",
            "username": email.split('@')[0],
            "avatar": None,
            "email": email
        }
        request.session["role"] = get_user_role(email)
        request.session["login_time"] = datetime.now().isoformat()
        
        if request.session["role"] == "admin":
             return RedirectResponse(url="/select-server", status_code=303)
        else:
             return RedirectResponse(url="/", status_code=303)
    else:
        masked = mask_email(email)
        return templates.TemplateResponse("verify_otp_page.html", {
            "request": request, "email": email, "masked_email": masked, "error": msg
        })

@router.get("/login")
async def login_page(request: Request):
    """Přesměrování na Discord OAuth."""
    if not DISCORD_CLIENT_ID or DISCORD_CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Discord OAuth není nakonfigurován. Kontaktujte administrátora."
        })
    
    orig_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    state_str = base64.urlsafe_b64encode(orig_host.encode()).decode() if orig_host else "default"
    
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
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
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Discord error: {error}"})
    if not code:
        return RedirectResponse(url="/login")
    
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(DISCORD_TOKEN_URL, data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI
            })
            
            if token_resp.status_code != 200:
                return templates.TemplateResponse("login.html", {"request": request, "error": "Ověření s Discordem selhalo."})
            
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
        return templates.TemplateResponse("login.html", {"request": request, "error": "Interní chyba při přihlášení."})

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
