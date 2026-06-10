"""Healthcheck endpoint — used by docker-compose and Cloud Run."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz():
    return {"status": "ok"}
