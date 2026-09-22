import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from web.backend.main import app, require_auth, require_admin

client = TestClient(app)

@pytest.mark.asyncio
async def test_require_auth_missing():
    request = MagicMock()
    request.session = {}
    request.url.path = "/protected"
    
    with pytest.raises(HTTPException) as excinfo:
        await require_auth(request)
    
    assert excinfo.value.status_code == 401
    assert "Not authenticated" in excinfo.value.detail

@pytest.mark.asyncio
async def test_require_auth_allowed_paths():
    request = MagicMock()
    request.session = {}
    request.url.path = "/login"
    
    # Nemělo by vyhodit výjimku
    result = await require_auth(request)
    assert result is None

@pytest.mark.asyncio
async def test_require_admin_missing_role():
    request = MagicMock()
    request.session = {"authenticated": True, "role": "user"}
    request.url.path = "/admin"
    
    with pytest.raises(HTTPException) as excinfo:
        await require_admin(request)
    
    assert excinfo.value.status_code == 403
    assert "Přístup pouze pro administrátory" in excinfo.value.detail

@pytest.mark.asyncio
async def test_require_admin_success():
    request = MagicMock()
    request.session = {"authenticated": True, "role": "admin"}
    request.url.path = "/admin"
    
    # Nemělo by vyhodit výjimku
    result = await require_admin(request)
    assert result is None

@pytest.mark.asyncio
async def test_require_admin_demo_role():
    request = MagicMock()
    request.session = {"authenticated": True, "role": "demo"}
    request.url.path = "/admin"
    
    with pytest.raises(HTTPException) as excinfo:
        await require_admin(request)
    
    assert excinfo.value.status_code == 403
    assert "Přístup pouze pro administrátory" in excinfo.value.detail

@pytest.mark.asyncio
async def test_require_auth_demo_role():
    request = MagicMock()
    request.session = {"authenticated": True, "role": "demo"}
    request.url.path = "/dashboard/123"
    
    # Nemělo by vyhodit výjimku pro demo roli na povolených cestách
    result = await require_auth(request)
    assert result is None

@pytest.mark.asyncio
async def test_csrf_valid():
    from web.backend.security import require_csrf
    import secrets
    request = MagicMock()
    token = secrets.token_urlsafe(32)
    request.session = {"csrf_token": token}
    request.headers = {"X-CSRF-Token": token}
    request.form = MagicMock(return_value={})
    
    await require_csrf(request) # no raise

@pytest.mark.asyncio
async def test_csrf_missing():
    from web.backend.security import require_csrf
    import secrets
    request = MagicMock()
    token = secrets.token_urlsafe(32)
    request.session = {"csrf_token": token}
    request.headers = {}
    request.form = MagicMock(return_value={})
    
    with pytest.raises(HTTPException) as excinfo:
        await require_csrf(request)
    assert excinfo.value.status_code == 403

@pytest.mark.asyncio
async def test_csrf_invalid():
    from web.backend.security import require_csrf
    import secrets
    request = MagicMock()
    request.session = {"csrf_token": "token1"}
    request.headers = {"X-CSRF-Token": "token2"}
    request.form = MagicMock(return_value={})
    
    with pytest.raises(HTTPException) as excinfo:
        await require_csrf(request)
    assert excinfo.value.status_code == 403

@pytest.mark.asyncio
async def test_csrf_missing_session():
    from web.backend.security import require_csrf
    import secrets
    request = MagicMock()
    request.session = {}
    request.headers = {"X-CSRF-Token": "token2"}
    request.form = MagicMock(return_value={})
    
    with pytest.raises(HTTPException) as excinfo:
        await require_csrf(request)
    assert excinfo.value.status_code == 403

def test_effective_redirect_uri_fallback(monkeypatch):
    from web.backend.routers.auth import get_effective_redirect_uri
    monkeypatch.delenv("DISCORD_REDIRECT_URI", raising=False)
    monkeypatch.setenv("DASHBOARD_PORT", "8095")
    assert get_effective_redirect_uri() == "http://localhost:8095/auth/callback"

def test_effective_redirect_uri_custom(monkeypatch):
    from web.backend.routers.auth import get_effective_redirect_uri
    monkeypatch.setenv("DISCORD_REDIRECT_URI", "https://example.com/auth/callback")
    assert get_effective_redirect_uri() == "https://example.com/auth/callback"


@pytest.mark.asyncio
async def test_dashboard_layout_save_and_reset():
    import json
    import secrets
    from web.backend.routers.settings import update_dashboard_layout, reset_dashboard_layout
    
    token = secrets.token_urlsafe(32)
    request = MagicMock()
    request.session = {
        "authenticated": True,
        "role": "admin",
        "csrf_token": token,
        "discord_user": {"id": "123", "username": "Admin"}
    }
    request.headers = {
        "X-CSRF-Token": token,
        "X-Requested-With": "XMLHttpRequest"
    }
    request.form = MagicMock(return_value={})

    # Test save layout
    order_json = json.dumps(["card_pred_msgs", "card_pred_members"])
    spans_json = json.dumps({"card_pred_msgs": 2})
    
    resp = await update_dashboard_layout(
        request=request,
        widget_order=order_json,
        widget_spans=spans_json,
        page="predictions",
        _=None
    )
    assert resp.status_code == 200
    assert request.session["predictions_order"] == ["card_pred_msgs", "card_pred_members"]
    assert request.session["dashboard_spans"]["card_pred_msgs"] == 2

    # Test reset layout
    resp_reset = await reset_dashboard_layout(
        request=request,
        page="predictions",
        _=None
    )
    assert resp_reset.status_code == 200
    assert "predictions_order" not in request.session
    assert "dashboard_spans" not in request.session


