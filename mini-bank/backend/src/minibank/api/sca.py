"""POST /api/sca/challenges/{id}/verify — finalises a pending transfer."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from minibank.db.models import User
from minibank.db.session import get_db
from minibank.deps import require_role
from minibank.schemas.transfer import ScaVerifyRequest, TransferResponse
from minibank.services import sca_service, transfer_service
from minibank.services.transfer_service import OverdraftError

router = APIRouter(prefix="/sca", tags=["sca"])


@router.post("/challenges/{challenge_id}/verify", response_model=TransferResponse)
def verify_challenge(
    challenge_id: UUID,
    body: ScaVerifyRequest,
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    # BUG-08 is in sca_service.verify itself — it ignores request_amount/iban.
    # We pass placeholders here because the real check should be against the
    # client-supplied current values, which v3 simplified clients don't send.
    try:
        pending = sca_service.verify(
            db,
            challenge_id=challenge_id,
            code=body.code,
            request_amount=Decimal(str(0)),
            request_dest_iban="",
        )
    except sca_service.ScaError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Execute the actual transfer
    try:
        trx = transfer_service.execute_transfer(
            db,
            initiator_id=user.id,
            source_account_id=UUID(pending["source_account_id"]),
            dest_iban=pending["dest_iban"],
            amount=Decimal(pending["amount"]),
            currency=pending["currency"],
            title=pending.get("title"),
            recipient_name=pending["recipient_name"],
        )
    except OverdraftError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    return TransferResponse(transaction_id=trx.id, status=trx.status)
