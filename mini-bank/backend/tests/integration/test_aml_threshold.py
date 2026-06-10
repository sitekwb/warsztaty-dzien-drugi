"""AML threshold: amount_in_eur > 15000 -> status=requires_review."""

import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Account, Currency, Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def env(tmp_path, monkeypatch):
    db_file = tmp_path / "aml.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    with session_module.SessionLocal() as db:
        cu = User(email="c@x.pl", password_hash=hash_password("pwd"),
                  role=Role.CUSTOMER, full_name="C")
        db.add(cu); db.flush()
        src = Account(owner_user_id=cu.id, holder_iban="PL12 1140 2004 0000 0000 0000 0001",
                      balance=Decimal("200000"), currency=Currency.PLN, opened_on=date(2024,1,1))
        db.add(src); db.commit()
        src_id = str(src.id)
    from minibank.main import app
    return app, src_id


def test_aml_threshold_triggers_review(env):
    app, src_id = env
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "c@x.pl", "password": "pwd"})
    # 70000 PLN / 4.30 PLN/EUR ~= 16279 EUR -> over 15000 -> requires_review
    r = c.post("/api/transfers", json={
        "source_account_id": src_id, "dest_iban": "PL99 9999 9999 9999 9999 9999 9999",
        "amount": "70000.00", "currency": "PLN", "title": "aml",
        "recipient_name": "Test Odbiorca"})
    assert r.status_code == 202
    challenge_id = r.json()["sca_challenge_id"]
    code = "".join(ch for ch in c.get("/api/notifications/me").json()[0]["body"] if ch.isdigit())[-6:]
    r2 = c.post(f"/api/sca/challenges/{challenge_id}/verify", json={"code": code})
    assert r2.json()["status"] == "requires_review"
