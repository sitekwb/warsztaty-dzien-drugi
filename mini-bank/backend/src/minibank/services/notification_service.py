"""In-app notifications + console log (mock SMS gateway)."""

from __future__ import annotations

import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.db.models import Notification


def send(db: Session, *, user_id: UUID, kind: str, body: str) -> Notification:
    n = Notification(user_id=user_id, kind=kind, body=body)
    db.add(n); db.flush(); db.refresh(n)
    print(f"[MOCK-SMS] to user {user_id}: {body}", file=sys.stderr, flush=True)
    return n


def list_for_user(db: Session, *, user_id: UUID, limit: int = 20) -> list[Notification]:
    stmt = (select(Notification).where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc()).limit(limit))
    return list(db.execute(stmt).scalars().all())
