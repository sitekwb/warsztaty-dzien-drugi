"""FastAPI dependency factory: gate a route on a valid JIT access grant.

The route must include the agent-supplied `X-Access-Grant-Id` header AND
a `customer_id` path param. The dependency calls
`access_grant_service.is_active_grant(db, grant_id, customer_id)`.

BUG-06 indirectly surfaces here: this middleware trusts is_active_grant,
which forgets the expires_at check. So a route protected by this
middleware will keep serving long after the grant has expired.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from minibank.db.session import get_db
from minibank.services import access_grant_service


def require_active_grant(customer_id_param: str = "customer_id") -> Callable:
    """Dependency factory. The protected route must declare a path param of
    name `customer_id_param` (default "customer_id").
    """

    def _checker(
        x_access_grant_id: str | None = Header(default=None, alias="X-Access-Grant-Id"),
        db: Session = Depends(get_db),
    ) -> UUID:
        if x_access_grant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-Access-Grant-Id header required",
            )
        try:
            grant_id = UUID(x_access_grant_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Access-Grant-Id is not a UUID",
            )
        return grant_id

    return _checker
