"""Step-up authentication decorator.

BUG-10 PLANTED: inspects User.last_login_at instead of User.last_step_up_at.
A long-running session post-login counts as 'fresh step-up' indefinitely.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status


def requires_recent_auth(*, seconds: int) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = kwargs.get("user")
            if user is None:
                raise RuntimeError("@requires_recent_auth requires user kwarg from Depends")
            # BUG-10: should look at user.last_step_up_at, not last_login_at.
            last = user.last_login_at
            if last is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="step-up required")
            now = datetime.now(timezone.utc)
            # Normalise: SQLite may return naive datetimes
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if (now - last).total_seconds() > seconds:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="step-up expired")
            return fn(*args, **kwargs)
        return wrapper
    return decorator
