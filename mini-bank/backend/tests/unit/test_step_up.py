"""@requires_recent_auth — fresh step-up required for sensitive actions.

BUG-10: decorator checks last_login_at instead of last_step_up_at.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Role, User
from minibank.deps import get_current_user
from minibank.middleware.step_up import requires_recent_auth
from minibank.services.auth_service import encode_jwt, hash_password


@pytest.fixture
def env(tmp_path, monkeypatch):
    db_file = tmp_path / "su.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    app = FastAPI()

    @app.get("/sensitive")
    @requires_recent_auth(seconds=60)
    def sensitive(user: User = Depends(get_current_user)):
        return {"ok": True}

    return app


def _make_user(login_at, step_up_at):
    with session_module.SessionLocal() as db:
        u = User(email="u@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="U",
                 last_login_at=login_at, last_step_up_at=step_up_at)
        db.add(u); db.commit(); db.refresh(u)
        return u.id


def test_recent_step_up_grants_access(env):
    """Both login and step-up recent → 200 (passes under correct impl and BUG-10)."""
    now = datetime.now(timezone.utc)
    user_id = _make_user(login_at=now - timedelta(seconds=10),
                         step_up_at=now - timedelta(seconds=10))
    c = TestClient(env)
    c.cookies.set("access_token", encode_jwt(user_id=str(user_id), role="customer"))
    assert c.get("/sensitive").status_code == 200


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-10: decorator uses last_login_at as proxy for step-up — fresh login bypasses gate",
    strict=False,
)
def test_recent_login_no_step_up_denied_BUG_10(env):
    """Fresh login should NOT count as step-up. BUG-10 wrongly accepts it."""
    now = datetime.now(timezone.utc)
    user_id = _make_user(login_at=now - timedelta(seconds=5),
                         step_up_at=None)
    c = TestClient(env)
    c.cookies.set("access_token", encode_jwt(user_id=str(user_id), role="customer"))
    assert c.get("/sensitive").status_code == 403
