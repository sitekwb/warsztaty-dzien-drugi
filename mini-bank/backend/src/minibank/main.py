"""FastAPI application entry point. Wires routers, CORS, settings."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from minibank.api import accounts, admin as admin_router_module, agent, auth, health, sca as sca_router_module, transfers
from minibank.api import notifications as notif_router_module
from minibank.api import consents as consents_router_module
from minibank.api import iban as iban_router_module
from minibank.config import get_settings


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="mini-bank",
        version="0.2.0",
        description="Interactive mBank workshop demo. PL UI, EN code.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api")
    app.include_router(accounts.router, prefix="/api")
    app.include_router(transfers.router, prefix="/api")
    app.include_router(sca_router_module.router, prefix="/api")
    app.include_router(agent.router, prefix="/api")
    app.include_router(admin_router_module.router, prefix="/api")
    app.include_router(notif_router_module.router, prefix="/api")
    app.include_router(consents_router_module.router, prefix="/api")
    app.include_router(iban_router_module.router, prefix="/api")

    # Serve built React SPA from STATIC_DIR if present (production single-container).
    static_dir = os.environ.get("STATIC_DIR")
    if static_dir and Path(static_dir).is_dir():
        # SPA fallback: any non-API path returns index.html so client-side router resolves it.
        app.mount("/assets", StaticFiles(directory=f"{static_dir}/assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            index = Path(static_dir) / "index.html"
            return FileResponse(index)

    return app


app = create_app()
