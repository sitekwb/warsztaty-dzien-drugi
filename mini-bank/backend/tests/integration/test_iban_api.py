"""Integration test for GET /api/iban/validate."""

from unittest.mock import AsyncMock, patch

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
    db_file = tmp_path / "iban.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    with session_module.SessionLocal() as db:
        u = User(email="c@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="C")
        db.add(u); db.commit()
    from minibank.main import app
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "c@x.pl", "password": "pwd"})
    return c


def test_validate_requires_auth(tmp_path, monkeypatch):
    db_file = tmp_path / "iban_noauth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    from minibank.main import app
    c = TestClient(app)
    r = c.get("/api/iban/validate", params={"iban": "PL21 1140 2004 0000 0000 0000 0000"})
    assert r.status_code == 401


def test_validate_invalid_iban(client):
    r = client.get("/api/iban/validate", params={"iban": "PL12"})
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert body["source"] == "local"


def test_validate_valid_iban_with_external_mocked(client):
    from minibank.services import iban_service
    iban_service._cache.clear()
    fake = {"valid": True, "bankData": {"name": "mBank S.A.", "bic": "BREXPLPWMBK"}}
    with patch.object(iban_service, "_fetch_openiban", new=AsyncMock(return_value=fake)):
        r = client.get("/api/iban/validate", params={"iban": "PL21 1140 2004 0000 0000 0000 0000"})
    body = r.json()
    assert body["valid"] is True
    assert body["bank_name"] == "mBank S.A."
    assert body["source"] == "external"
