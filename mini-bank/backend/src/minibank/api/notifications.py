"""Customer-facing notification queue."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from minibank.db.models import User
from minibank.db.session import get_db
from minibank.deps import get_current_user
from minibank.services.notification_service import list_for_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me")
def my_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = list_for_user(db, user_id=user.id)
    return [
        {"id": str(r.id), "kind": r.kind, "body": r.body,
         "created_at": r.created_at.isoformat()}
        for r in rows
    ]
