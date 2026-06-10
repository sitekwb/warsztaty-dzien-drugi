"""GET /api/admin/audit/verify — walks the chain and reports first break."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Role, User
from minibank.services import audit_service
from minibank.services.auth_service import hash_password


@pytest.fixture
def client_and_admin(tmp_path, monkeypatch):
    db_file = tmp_path / "av.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as db:
        admin = User(email="ad@x.pl", password_hash=hash_password("pwd"),
                     role=Role.ADMIN, full_name="Ad")
        db.add(admin)
        db.commit()
        db.refresh(admin)
        # seed 3 chained entries
        for action in ("a", "b", "c"):
            audit_service.record(db, actor_user_id=admin.id, action=action)
        db.commit()

    from minibank.main import app
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": "ad@x.pl", "password": "pwd"})
    assert r.status_code == 200
    return c


def test_verify_ok_chain(client_and_admin):
    r = client_and_admin.get("/api/admin/audit/verify")
    assert r.status_code == 200
    body = r.json()
    assert body == {"ok": True, "entries": 3, "first_broken_id": None}


def test_verify_detects_tampering(client_and_admin):
    with session_module.SessionLocal() as db:
        rows = db.execute(text("SELECT id FROM audit_log ORDER BY id")).fetchall()
        db.execute(text("UPDATE audit_log SET action = 'tampered' WHERE id = :i"),
                   {"i": rows[1][0]})
        db.commit()

    r = client_and_admin.get("/api/admin/audit/verify")
    body = r.json()
    assert body["ok"] is False
    assert body["first_broken_id"] is not None


def test_verify_requires_admin(client_and_admin):
    client_and_admin.post("/api/auth/logout")
    with session_module.SessionLocal() as db:
        c = User(email="c@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="C")
        db.add(c); db.commit()
    client_and_admin.post("/api/auth/login", json={"email": "c@x.pl", "password": "pwd"})
    r = client_and_admin.get("/api/admin/audit/verify")
    assert r.status_code == 403
