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
