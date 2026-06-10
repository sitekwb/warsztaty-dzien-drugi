"""audit_service.record builds a SHA-256 chain via prev_hash/row_hash."""

import hashlib
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
        u = User(email="a@x.pl", password_hash="x", role=Role.AGENT, full_name="A")
        s.add(u)
        s.commit()
        s.refresh(u)
        s.actor_id = u.id
        yield s


def test_first_entry_has_genesis_prev_hash(db):
    e = audit_service.record(db, actor_user_id=db.actor_id, action="first")
    db.commit()
    assert e.prev_hash == "0" * 64
    assert e.row_hash is not None and len(e.row_hash) == 64


def test_second_entry_links_to_first(db):
    e1 = audit_service.record(db, actor_user_id=db.actor_id, action="first")
    db.commit()
    e2 = audit_service.record(db, actor_user_id=db.actor_id, action="second")
    db.commit()
    assert e2.prev_hash == e1.row_hash
    assert e2.row_hash != e1.row_hash


def test_row_hash_is_deterministic(db):
    e = audit_service.record(
        db,
        actor_user_id=db.actor_id,
        action="x",
        target_type="t",
        target_id="id1",
        payload={"k": "v"},
    )
    db.commit()
    expected_input = (
        e.prev_hash
        + "|" + str(e.actor_user_id)
        + "|" + "x"
        + "|" + "t"
        + "|" + "id1"
        + "|" + '{"k": "v"}'
    )
    assert e.row_hash == hashlib.sha256(expected_input.encode("utf-8")).hexdigest()
