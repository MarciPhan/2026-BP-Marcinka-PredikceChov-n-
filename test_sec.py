from fastapi.testclient import TestClient
from web.backend.main import app

client = TestClient(app)
app.dependency_overrides.clear()
resp = client.post("/api/admin/support-channels", json={"support_channels": []}, headers={"Cookie": "session=dummy;"})
print("STATUS CODE:", resp.status_code)
print("BODY:", resp.json() if resp.status_code == 200 else resp.text)
