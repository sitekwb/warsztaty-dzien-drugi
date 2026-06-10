"""Customer transfer endpoint. v3: returns 202 + SCA challenge; transfer
executed by /api/sca/challenges/{id}/verify."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from minibank.db.models import User
from minibank.db.session import get_db
from minibank.deps import require_role
from minibank.middleware.audit import audited
from minibank.middleware.idempotency import cache_lookup, cache_store, compute_request_hash
from minibank.schemas.transfer import (
    TransferInitiateResponse,
    TransferRequest,
)
from minibank.services import account_service, sca_service
from minibank.services.notification_service import send as send_notification

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferInitiateResponse, status_code=status.HTTP_202_ACCEPTED)
@audited(action="transfer_initiated", target_type="transaction")
def initiate_transfer(
    payload: TransferRequest,
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    # Idempotency check
    parsed_key: UUID | None = None
    request_hash: str | None = None
    if idempotency_key is not None:
        try:
            parsed_key = UUID(idempotency_key)
        except ValueError:
            raise HTTPException(status_code=400, detail="Idempotency-Key must be a UUID")
        request_hash = compute_request_hash(payload.model_dump(mode="json"))
        cached_body, cached_status = cache_lookup(db, key=parsed_key, request_hash=request_hash)
        if cached_status is not None:
            return JSONResponse(status_code=cached_status, content=cached_body)

    src = account_service.get_account(db, payload.source_account_id)
    if src is None or src.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="source account not found")

    # Create SCA challenge — DO NOT execute the transfer yet
    pending = payload.model_dump(mode="json")
    pending["initiator_user_id"] = str(user.id)
    ch, code = sca_service.create_challenge(
        db,
        user_id=user.id,
        amount=payload.amount,
        dest_iban=payload.dest_iban,
        pending_payload=pending,
    )
    send_notification(
        db,
        user_id=user.id,
        kind="sca_otp",
        body=f"mini-bank: przelew {payload.amount} {payload.currency} -> {payload.dest_iban} kod: {code}",
    )

    response_body = {
        "sca_challenge_id": str(ch.id),
        "expires_at": ch.expires_at.isoformat(),
    }

    if parsed_key is not None and request_hash is not None:
        cache_store(db, key=parsed_key, user_id=user.id, request_hash=request_hash,
                    response_body=response_body, status_code=202)
    db.commit()
    return response_body


@router.post("/{transaction_id}/approve")
def approve_transfer(
    transaction_id: UUID,
    user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
):
    from minibank.db.models import Transaction, Account
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=404, detail="transaction not found")
    if not t.requires_dual_approval or t.status != "requires_dual_approval":
        raise HTTPException(status_code=400, detail="transaction not pending dual approval")
    if t.initiated_by_user_id == user.id:
        raise HTTPException(status_code=403, detail="approver must differ from initiator")
    src = db.get(Account, t.source_account_id)
    if src is None or src.balance + src.overdraft_limit < t.amount:
        raise HTTPException(status_code=400, detail="insufficient funds at approval time")
    src.balance -= t.amount
    if t.dest_account_id is not None:
        dst = db.get(Account, t.dest_account_id)
        if dst is not None and dst.status == "open":
            dst.balance += t.amount
    t.status = "completed"
    t.approved_by_user_id = user.id
    db.commit()
    db.refresh(t)
    return {"transaction_id": str(t.id), "status": t.status}
