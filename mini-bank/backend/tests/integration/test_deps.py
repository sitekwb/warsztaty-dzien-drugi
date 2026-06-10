"""Tests for FastAPI deps: get_current_user from JWT cookie, role checks."""

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Role, User
from minibank.db import session as session_module
from minibank.deps import get_current_user, require_role
from minibank.services.auth_service import encode_jwt, hash_password


@pytest.fixture
def app_and_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    app = FastAPI()

    @app.get("/whoami")
    def whoami(user: User = Depends(get_current_user)):
        return {"id": str(user.id), "role": user.role.value}

    @app.get("/agent-only")
    def agent_only(user: User = Depends(require_role("agent"))):
        return {"ok": True}

    with session_module.SessionLocal() as db:
        u = User(
            email="x@x.pl",
            password_hash=hash_password("pwd"),
            role=Role.CUSTOMER,
            full_name="X",
        )
        db.add(u)
        db.commit()
        yield app, u


def test_whoami_with_valid_cookie(app_and_db):
    app, user = app_and_db
    client = TestClient(app)
    token = encode_jwt(user_id=str(user.id), role="customer")
    r = client.get("/whoami", cookies={"access_token": token})
    assert r.status_code == 200
    assert r.json()["role"] == "customer"


def test_whoami_no_cookie_401(app_and_db):
    app, _ = app_and_db
    client = TestClient(app)
    r = client.get("/whoami")
    assert r.status_code == 401


def test_agent_only_rejects_customer(app_and_db):
    app, user = app_and_db
    client = TestClient(app)
    token = encode_jwt(user_id=str(user.id), role="customer")
    r = client.get("/agent-only", cookies={"access_token": token})
    assert r.status_code == 403
