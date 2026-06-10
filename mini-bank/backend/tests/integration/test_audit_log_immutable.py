"""Test that audit_log is append-only via DB trigger.

BUG-05: the v2 Alembic migration does NOT create a BEFORE UPDATE OR DELETE
trigger on audit_log. So mutation is technically allowed. Fix lands in
solutions branch: add trigger that raises an error on UPDATE/DELETE.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import AuditLogEntry, Role, User


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        u = User(email="a@x.pl", password_hash="x", role=Role.AGENT, full_name="A")
        s.add(u)
        s.flush()
        e = AuditLogEntry(actor_user_id=u.id, action="test", payload={"k": "v"})
        s.add(e)
        s.commit()
        s.refresh(e)
        yield s, e


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-05: no BEFORE UPDATE OR DELETE trigger on audit_log; mutation succeeds",
    strict=False,
)
def test_audit_log_update_is_blocked_BUG_05(session):
    sess, entry = session
    with pytest.raises(Exception):
        sess.execute(
            text("UPDATE audit_log SET action = :new WHERE id = :i"),
            {"new": "tampered", "i": entry.id},
        )
        sess.commit()


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-05: no BEFORE UPDATE OR DELETE trigger; DELETE succeeds",
    strict=False,
)
def test_audit_log_delete_is_blocked_BUG_05(session):
    sess, entry = session
    with pytest.raises(Exception):
        sess.execute(text("DELETE FROM audit_log WHERE id = :i"), {"i": entry.id})
        sess.commit()
