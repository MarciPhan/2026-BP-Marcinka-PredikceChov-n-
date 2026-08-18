import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Fix import path for testing
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from web.backend.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_login_redirect():
    response = client.get("/commands", follow_redirects=False)
    # The middleware/dependency redirects unauthenticated users to "/" (or raises 401 which redirects)
    assert response.status_code in [302, 303, 307]

def test_favicon():
    response = client.get("/favicon.ico", follow_redirects=False)
    assert response.status_code in [302, 303, 307, 200]
