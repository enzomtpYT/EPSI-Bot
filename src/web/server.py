"""Asynchronous web server launcher for EPSI Bot."""

from __future__ import annotations

import logging

import uvicorn

from config import settings
from web.app import create_web_app

logger = logging.getLogger(__name__)


def create_uvicorn_server() -> uvicorn.Server:
    """Create configured Uvicorn Server instance."""
    app = create_web_app()
    config = uvicorn.Config(
        app=app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="warning",
        access_log=False,
    )
    return uvicorn.Server(config)
