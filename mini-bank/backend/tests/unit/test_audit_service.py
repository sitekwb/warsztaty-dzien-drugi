"""Tests for DB-backed audit_service. BUG-07 lives here: payload is stored
as-is, including any PESEL field, instead of pseudonymizing it.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import AuditLogEntry, Role, User
from minibank.services import audit_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        u = User(email="actor@x.pl", password_hash="x", role=Role.AGENT, full_name="A")
        s.add(u)
        s.commit()
        s.refresh(u)
        s.actor_id = u.id  # type: ignore[attr-defined]
        yield s


def test_record_writes_one_entry(db):
    entry = audit_service.record(
        db,
        actor_user_id=db.actor_id,
        action="transfer_initiated",
        target_type="transaction",
        target_id="abc-123",
        payload={"amount": "100.00"},
    )
    db.commit()
    assert entry.id is not None
    fetched = db.execute(select(AuditLogEntry)).scalar_one()
    assert fetched.action == "transfer_initiated"
    assert fetched.payload == {"amount": "100.00"}


def test_record_requires_actor(db):
    with pytest.raises(ValueError):
        audit_service.record(
            db,
            actor_user_id=None,  # type: ignore[arg-type]
            action="anything",
        )


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-07: audit_service writes payload as-is, PESEL plaintext leaks",
    strict=False,
)
def test_record_persists_payload_including_pesel_plaintext_BUG_07(db):
    """BUG-07: audit_service.record() stores payload as-is. If a caller
    includes a pesel field, the plaintext lands in audit_log. Banking apps
    must pseudonymize PESEL before logging. The fix (solutions branch):
    detect 'pesel' key and replace with sha256 hash.
    """
    entry = audit_service.record(
        db,
        actor_user_id=db.actor_id,
        action="view_customer",
        target_type="user",
        target_id="customer-id",
        payload={"pesel": "75102612345", "note": "lookup"},
    )
    db.commit()
    pesel_in_payload = entry.payload.get("pesel")
    # FAILS while BUG-07 active: plaintext PESEL ends up in payload.
    # Correct (solutions): stored value should NOT equal the plaintext PESEL
    # (e.g. would be a hash or be removed).
    assert pesel_in_payload != "75102612345", (
        "BUG-07: plaintext PESEL leaked into audit_log payload"
    )
