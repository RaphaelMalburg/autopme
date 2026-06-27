from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_auth_login_flow():
    original = settings.admin_password
    settings.admin_password = "democonsultoria123"
    try:
        client = TestClient(app)
        blocked = client.get("/api/scenarios/niches")
        assert blocked.status_code == 401

        login = client.post("/api/auth/login", json={"password": "democonsultoria123"})
        assert login.status_code == 200

        ok = client.get("/api/scenarios/niches")
        assert ok.status_code == 200
    finally:
        settings.admin_password = original
