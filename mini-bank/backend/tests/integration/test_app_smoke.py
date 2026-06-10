"""End-to-end smoke test: app boots, healthz works, login+me round-trip."""

import pytest
from fastapi.testclient import TestClient

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    from minibank.main import app
    with session_module.SessionLocal() as db:
        db.add(User(
            email="smoke@minibank.pl",
            password_hash=hash_password("pwd"),
            role=Role.CUSTOMER,
            full_name="Smoke User",
        ))
        db.commit()
    return TestClient(app)


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_then_me(client):
    r = client.post("/api/auth/login", json={"email": "smoke@minibank.pl", "password": "pwd"})
    assert r.status_code == 200
    assert r.cookies.get("access_token") is not None
    r2 = client.get("/api/auth/me")
    assert r2.status_code == 200
    assert r2.json()["full_name"] == "Smoke User"


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "smoke@minibank.pl", "password": "WRONG"})
    assert r.status_code == 401
