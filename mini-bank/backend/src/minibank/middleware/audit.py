"""@audited decorator for FastAPI endpoints — writes one audit_log row per call.

Usage:
    @router.post("/transfers")
    @audited(action="transfer_initiated")
    def initiate_transfer(payload, user, db):
        ...

The decorator looks at the wrapped function's kwargs for `user` (from
Depends(require_role) / get_current_user) and `db` (from Depends(get_db)).
If either is missing, the decorator raises at call time — fail loudly so the
wiring is caught in tests.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from minibank.services import audit_service


def audited(*, action: str, target_type: str | None = None) -> Callable:
    """Decorator factory: write an audit_log entry around a FastAPI endpoint.

    The wrapped function must receive `user` and `db` as keyword arguments
    (the usual FastAPI dependency-injection pattern).
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = kwargs.get("user")
            db = kwargs.get("db")
            if user is None or db is None:
                raise RuntimeError(
                    f"@audited requires `user` and `db` kwargs; got user={user!r}, db={db!r}"
                )
            result = fn(*args, **kwargs)
            audit_service.record(
                db,
                actor_user_id=user.id,
                action=action,
                target_type=target_type,
            )
            db.commit()
            return result

        return wrapper

    return decorator
