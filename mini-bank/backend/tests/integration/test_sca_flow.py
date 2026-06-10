"""Full SCA flow: initiate -> 202 + challenge -> verify -> debit applied."""

import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Account, Currency, Notification, Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "sca.db"
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
        src_id = str(src.id); dst_iban = dst.holder_iban; user_id = u.id

    from minibank.main import app
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "t@x.pl", "password": "pwd"})
    return c, src_id, dst_iban, user_id


def test_post_transfers_returns_202_with_challenge(client):
    c, src_id, dst_iban, user_id = client
    r = c.post("/api/transfers", json={
        "source_account_id": src_id, "dest_iban": dst_iban,
        "amount": "10.00", "currency": "PLN", "title": "sca",
        "recipient_name": "Jan Kowalski",
    })
    assert r.status_code == 202
    body = r.json()
    assert "sca_challenge_id" in body

    with session_module.SessionLocal() as db:
        notes = db.execute(select(Notification).where(Notification.user_id == user_id)).scalars().all()
    assert len(list(notes)) >= 1

    # Refetch to get fresh list (above was iterator-consumed); easier: read again
    with session_module.SessionLocal() as db:
        notes = list(db.execute(select(Notification).where(Notification.user_id == user_id)).scalars().all())
    assert len(notes) == 1
    assert "10.00 PLN" in notes[0].body
    code = "".join(ch for ch in notes[0].body if ch.isdigit())[-6:]
    assert len(code) == 6

    challenge_id = body["sca_challenge_id"]
    r2 = c.post(f"/api/sca/challenges/{challenge_id}/verify", json={"code": code})
    assert r2.status_code == 200
    assert r2.json()["status"] == "completed"

    with session_module.SessionLocal() as db:
        from sqlalchemy import select as _select
        from minibank.db.models import Transaction
        tx = db.execute(_select(Transaction).where(Transaction.initiated_by_user_id == user_id)).scalar_one()
    assert tx.recipient_name == "Jan Kowalski"


def test_post_transfers_missing_recipient_name_422(client):
    c, src_id, dst_iban, _ = client
    r = c.post("/api/transfers", json={
        "source_account_id": src_id, "dest_iban": dst_iban,
        "amount": "10.00", "currency": "PLN", "title": "sca",
    })
    assert r.status_code == 422
