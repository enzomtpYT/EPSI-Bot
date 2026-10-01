"""FastAPI application setup for EPSI Bot WebUI."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from web.routes_api import api_router
from web.routes_auth import auth_router

logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_web_app() -> FastAPI:
    """Create and configure the FastAPI web application."""
    app = FastAPI(
        title="EPSI Schedule WebUI",
        description="Web interface and OAuth2 portal for EPSI Discord Bot",
        version="2.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    # Session middleware for Discord OAuth2 state
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="epsi_session",
        max_age=86400 * 30,  # 30 days
        same_site="lax",
        https_only=False,  # Set to true in strict HTTPS production if behind reverse proxy
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static assets
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # PWA Special routes
    @app.get("/manifest.json")
    async def get_manifest() -> FileResponse:
        return FileResponse(STATIC_DIR / "manifest.json", media_type="application/json")

    @app.get("/service-worker.js")
    async def get_service_worker() -> FileResponse:
        return FileResponse(
            STATIC_DIR / "service-worker.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )

    # Main WebUI route
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "oauth_configured": bool(
                    settings.discord_client_id and settings.discord_client_secret
                ),
                "share_token": None,
            },
        )

    # Shared schedule direct link route
    @app.get("/share/{token}", response_class=HTMLResponse)
    async def share_page(request: Request, token: str) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "oauth_configured": bool(
                    settings.discord_client_id and settings.discord_client_secret
                ),
                "share_token": token,
            },
        )

    # Include Routers
    app.include_router(auth_router)
    app.include_router(api_router)

    return app
