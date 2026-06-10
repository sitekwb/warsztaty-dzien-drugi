"""Tests for /api/agent/access-grants endpoints (POST, GET active, DELETE)."""

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
    db_file = tmp_path / "ag.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as db:
        agent = User(email="ag@x.pl", password_hash=hash_password("pwd"), role=Role.AGENT, full_name="Ag")
        customer = User(email="c@x.pl", password_hash=hash_password("pwd"), role=Role.CUSTOMER, full_name="C")
        db.add_all([agent, customer])
        db.commit()
        db.refresh(agent); db.refresh(customer)
        customer_id = str(customer.id)

    from minibank.main import app
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": "ag@x.pl", "password": "pwd"})
    assert r.status_code == 200
    return c, customer_id


def test_create_grant_returns_id(client):
    c, customer_id = client
    r = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "TCK-1", "reason": "Investigate", "ttl_minutes": 30},
    )
    assert r.status_code == 201
    body = r.json()
    assert "id" in body and "expires_at" in body


def test_list_active_grants(client):
    c, customer_id = client
    c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "TCK-2", "reason": "x", "ttl_minutes": 15},
    )
    r = c.get("/api/agent/access-grants/active")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) >= 1
    assert arr[0]["ticket_id"] == "TCK-2"


def test_revoke_grant(client):
    c, customer_id = client
    r = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "TCK-3", "reason": "x", "ttl_minutes": 15},
    )
    grant_id = r.json()["id"]
    r2 = c.delete(f"/api/agent/access-grants/{grant_id}")
    assert r2.status_code == 200
    r3 = c.get("/api/agent/access-grants/active")
    assert all(g["id"] != grant_id for g in r3.json())


def test_create_grant_validation(client):
    c, customer_id = client
    r = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "", "reason": "x", "ttl_minutes": 15},
    )
    assert r.status_code == 422  # empty ticket_id
    r2 = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "T", "reason": "x", "ttl_minutes": 9999},
    )
    assert r2.status_code == 422  # ttl out of range
