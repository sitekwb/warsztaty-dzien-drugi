"""GET /api/notifications/me returns the customer's own notifications."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Notification, Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "n.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as db:
        u = User(email="n@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="N")
        db.add(u); db.flush()
        db.add(Notification(user_id=u.id, kind="sca_otp", body="kod 123456"))
        db.commit()

    from minibank.main import app
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "n@x.pl", "password": "pwd"})
    return c


def test_list_my_notifications(client):
    r = client.get("/api/notifications/me")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) == 1
    assert arr[0]["body"] == "kod 123456"
