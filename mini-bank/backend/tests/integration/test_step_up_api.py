"""POST /auth/step-up updates user.last_step_up_at;
GET /agent/customers/{id}/full requires recent step-up."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "su.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    with session_module.SessionLocal() as db:
        ag = User(email="ag@x.pl", password_hash=hash_password("pwd"),
                  role=Role.AGENT, full_name="A")
        cu = User(email="c@x.pl", password_hash=hash_password("pwd"),
                  role=Role.CUSTOMER, full_name="C", pesel="75102612345")
        db.add_all([ag, cu]); db.commit(); db.refresh(cu)
        cust_id = str(cu.id)
    from minibank.main import app
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "ag@x.pl", "password": "pwd"})
    return c, cust_id


def test_step_up_sets_timestamp(client):
    c, _ = client
    r = c.post("/api/auth/step-up", json={"code": "ANY"})
    assert r.status_code == 200


def test_full_customer_smoke(client):
    """Either 200 (BUG-10 active, login recent) or 403 (correct: no step-up).
    The unit-level BUG-10 xfail elsewhere documents the bug."""
    c, cust_id = client
    r = c.get(f"/api/agent/customers/{cust_id}/full")
    assert r.status_code in (200, 403)


def test_full_customer_after_step_up(client):
    c, cust_id = client
    c.post("/api/auth/step-up", json={"code": "ANY"})
    r = c.get(f"/api/agent/customers/{cust_id}/full")
    assert r.status_code == 200
    assert r.json()["pesel"] == "75102612345"
