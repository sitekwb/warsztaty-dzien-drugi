"""Test the @audited decorator integrates with FastAPI endpoints."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import AuditLogEntry, Role, User
from minibank.db.session import get_db
from minibank.deps import get_current_user
from minibank.middleware.audit import audited
from minibank.services.auth_service import encode_jwt, hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "audited.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    app = FastAPI()

    @app.post("/poke")
    @audited(action="poke")
    def poke(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        return {"ok": True}

    with session_module.SessionLocal() as db:
        u = User(
            email="a@x.pl",
            password_hash=hash_password("pwd"),
            role=Role.CUSTOMER,
            full_name="A",
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        user_id = u.id

    c = TestClient(app)
    token = encode_jwt(user_id=str(user_id), role="customer")
    c.cookies.set("access_token", token)
    return c, user_id


def test_audited_writes_entry(client):
    c, user_id = client
    r = c.post("/poke")
    assert r.status_code == 200

    with session_module.SessionLocal() as db:
        entries = list(db.execute(select(AuditLogEntry)).scalars().all())
    assert len(entries) == 1
    assert entries[0].action == "poke"
    assert entries[0].actor_user_id == user_id
