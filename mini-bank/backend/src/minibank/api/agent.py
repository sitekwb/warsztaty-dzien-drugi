"""Agent-facing endpoints. In v1, agents can LIST customers and see basic detail,
but CANNOT access customer accounts/transactions (that requires JIT grant in v2)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from minibank.db.models import User
from minibank.db.session import get_db
from minibank.deps import require_role
from minibank.middleware.access_grant import require_active_grant
from minibank.middleware.step_up import requires_recent_auth
from minibank.schemas.access_grant import CreateGrantRequest, GrantResponse
from minibank.schemas.account import AccountResponse, TransactionResponse
from minibank.schemas.user import UserMasked
from minibank.services import access_grant_service, account_service, agent_service

router = APIRouter(prefix="/agent", tags=["agent"])


def _to_masked(user: User) -> UserMasked:
    return UserMasked(
        id=user.id,
        email=user.email,
        role=user.role.value,
        full_name=user.full_name,
        pesel_masked=account_service.mask_pesel(user.pesel),
        citizenship=user.citizenship,
    )


@router.get("/customers", response_model=list[UserMasked])
def list_customers(
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    _agent: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    customers = agent_service.list_customers(db, search=search, limit=page_size, offset=offset)
    return [_to_masked(c) for c in customers]


@router.get("/customers/{customer_id}", response_model=UserMasked)
def get_customer_detail(
    customer_id: UUID,
    _agent: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    c = agent_service.get_customer(db, customer_id)
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")
    return _to_masked(c)


@router.get("/customers/{customer_id}/full")
@requires_recent_auth(seconds=60)
def get_customer_full(
    customer_id: UUID,
    user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    c = agent_service.get_customer(db, customer_id)
    if c is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return {
        "id": str(c.id), "email": c.email, "full_name": c.full_name,
        "pesel": c.pesel, "citizenship": c.citizenship,
    }


@router.post("/access-grants", response_model=GrantResponse, status_code=status.HTTP_201_CREATED)
def create_access_grant(
    payload: CreateGrantRequest,
    user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    grant = access_grant_service.create_grant(
        db,
        agent_user_id=user.id,
        customer_id=payload.customer_id,
        ticket_id=payload.ticket_id,
        reason=payload.reason,
        ttl_minutes=payload.ttl_minutes,
    )
    db.commit()
    db.refresh(grant)
    return grant


@router.get("/access-grants/active", response_model=list[GrantResponse])
def list_active_access_grants(
    user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    return access_grant_service.list_active_for_agent(db, agent_user_id=user.id)


@router.delete("/access-grants/{grant_id}")
def revoke_access_grant(
    grant_id: UUID,
    user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    grant = access_grant_service.revoke_grant(db, grant_id=grant_id, agent_user_id=user.id)
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="grant not found")
    db.commit()
    return {"ok": True}


@router.get(
    "/customers/{customer_id}/accounts",
    response_model=list[AccountResponse],
)
def get_customer_accounts(
    customer_id: UUID,
    grant_id: UUID = Depends(require_active_grant()),
    _user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    if not access_grant_service.is_active_grant(db, grant_id=grant_id, customer_id=customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="grant not active for this customer",
        )
    return account_service.list_customer_accounts(db, customer_id)


@router.get(
    "/customers/{customer_id}/transactions",
    response_model=list[TransactionResponse],
)
def get_customer_transactions(
    customer_id: UUID,
    grant_id: UUID = Depends(require_active_grant()),
    _user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    if not access_grant_service.is_active_grant(db, grant_id=grant_id, customer_id=customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="grant not active for this customer",
        )
    accounts = account_service.list_customer_accounts(db, customer_id)
    rows: list = []
    for acc in accounts:
        rows.extend(account_service.list_account_transactions(db, acc.id, limit=limit, offset=offset))
    return rows[:limit]


@router.get("/supervisor/review-queue")
def review_queue(
    user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
):
    from minibank.db.models import Transaction
    from sqlalchemy import select, or_
    stmt = (select(Transaction)
            .where(or_(Transaction.status == "requires_dual_approval",
                       Transaction.status == "requires_review"))
            .order_by(Transaction.created_at.desc()))
    rows = list(db.execute(stmt).scalars().all())
    return [
        {"id": str(t.id), "amount": str(t.amount), "currency": t.currency.value,
         "status": t.status, "dest_iban": t.dest_iban,
         "created_at": t.created_at.isoformat()}
        for t in rows
    ]
