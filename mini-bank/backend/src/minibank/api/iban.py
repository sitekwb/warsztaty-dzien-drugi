"""IBAN validation endpoint — auth-gated proxy over iban_service."""

from fastapi import APIRouter, Depends, Query

from minibank.db.models import User
from minibank.deps import get_current_user
from minibank.services import iban_service

router = APIRouter(prefix="/iban", tags=["iban"])


@router.get("/validate")
async def validate_iban(
    iban: str = Query(..., min_length=4, max_length=40),
    _user: User = Depends(get_current_user),
):
    return await iban_service.validate(iban)
