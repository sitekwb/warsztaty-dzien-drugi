"""Agent requests consent; customer approves; agent acts."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def env(tmp_path, monkeypatch):
    db_file = tmp_path / "co.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    with session_module.SessionLocal() as db:
        ag = User(email="ag@x.pl", password_hash=hash_password("pwd"), role=Role.AGENT, full_name="A")
        cu = User(email="c@x.pl", password_hash=hash_password("pwd"), role=Role.CUSTOMER, full_name="C")
        db.add_all([ag, cu]); db.commit(); db.refresh(cu); db.refresh(ag)
        cu_id = str(cu.id); ag_id = str(ag.id)
    from minibank.main import app
    return app, cu_id, ag_id


def test_consent_request_then_approve(env):
    app, cust_id, ag_id = env
    ag_client = TestClient(app)
    ag_client.post("/api/auth/login", json={"email": "ag@x.pl", "password": "pwd"})

    r = ag_client.post("/api/consents", json={
        "customer_id": cust_id, "scope": "read", "ttl_minutes": 30,
    })
    assert r.status_code == 201
    consent_id = r.json()["id"]

    cu_client = TestClient(app)
    cu_client.post("/api/auth/login", json={"email": "c@x.pl", "password": "pwd"})

    r2 = cu_client.get("/api/consents/pending")
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = cu_client.post(f"/api/consents/{consent_id}/approve")
    assert r3.status_code == 200

    r4 = cu_client.get("/api/consents/pending")
    assert len(r4.json()) == 0
