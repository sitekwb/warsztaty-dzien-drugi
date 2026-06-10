"""Idempotency on POST /api/transfers — second identical POST returns cached
response without performing the transfer again."""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Account, Currency, Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "ti.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as db:
        u = User(email="t@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="T")
        db.add(u); db.flush()
        src = Account(owner_user_id=u.id, holder_iban="PL12 1140 2004 0000 0000 0000 0001",
                      balance=Decimal("500.00"), currency=Currency.PLN, opened_on=date(2024, 1, 1))
        dst = Account(owner_user_id=u.id, holder_iban="PL12 1140 2004 0000 0000 0000 0002",
                      balance=Decimal("0.00"), currency=Currency.PLN, opened_on=date(2024, 1, 1))
        db.add_all([src, dst]); db.commit()
        src_id = str(src.id); dst_iban = dst.holder_iban

    from minibank.main import app
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "t@x.pl", "password": "pwd"})
    return c, src_id, dst_iban


def test_replay_same_key_same_payload_returns_cached(client):
    c, src_id, dst_iban = client
    key = str(uuid4())
    payload = {"source_account_id": src_id, "dest_iban": dst_iban,
               "amount": "10.00", "currency": "PLN", "title": "idem",
               "recipient_name": "Test Odbiorca"}
    r1 = c.post("/api/transfers", json=payload, headers={"Idempotency-Key": key})
    assert r1.status_code in (201, 202)
    r2 = c.post("/api/transfers", json=payload, headers={"Idempotency-Key": key})
    assert r2.status_code == r1.status_code
    assert r2.json() == r1.json()
