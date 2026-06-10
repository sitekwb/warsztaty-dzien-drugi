"""Agent-facing queries: list customers, search, look up by id.

In v1 the agent can only LIST customers and see their basic details (with
masked PESEL). Reading customer accounts/transactions requires a JIT access
grant — added in v2.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from minibank.db.models import Role, User


def list_customers(
    db: Session,
    *,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[User]:
    """Return customer users, optionally filtered by partial email/full_name match."""
    stmt = select(User).where(User.role == Role.CUSTOMER)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    stmt = stmt.order_by(User.full_name).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def get_customer(db: Session, customer_id: UUID) -> User | None:
    """Return user iff they exist AND are a customer; else None."""
    user = db.get(User, customer_id)
    if user is None or user.role != Role.CUSTOMER:
        return None
    return user
