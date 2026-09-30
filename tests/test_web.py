"""Tests for FastAPI WebUI and API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from dateutil import parser
from httpx import ASGITransport, AsyncClient

from database import init_db, set_database_url
from models import CourseEvent
from web.app import create_web_app


@pytest.fixture(autouse=True)
async def setup_test_db():
    set_database_url("sqlite+aiosqlite:///:memory:")
    await init_db()


@pytest.mark.asyncio
async def test_index_page():
    app = create_web_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "EPSI Emploi du temps" in response.text
        assert "discordLoginBtn" in response.text


@pytest.mark.asyncio
async def test_static_and_pwa_routes():
    app = create_web_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp_manifest = await client.get("/manifest.json")
        assert resp_manifest.status_code == 200
        assert resp_manifest.json()["short_name"] == "EPSI EDT"

        resp_sw = await client.get("/service-worker.js")
        assert resp_sw.status_code == 200
        assert "Service Worker" in resp_sw.text


@pytest.mark.asyncio
async def test_api_me_unauthenticated():
    app = create_web_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/me")
        assert response.status_code == 200
        data = response.json()
        assert data["logged_in"] is False


@pytest.mark.asyncio
async def test_api_settings_unauthenticated():
    app = create_web_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/settings", json={"daily_notifications": True})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_schedule_week_missing_url():
    app = create_web_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/schedule/week?date=2026-10-12")
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_api_schedule_week_success():
    app = create_web_app()
    mock_courses = [
        CourseEvent(
            uid="event-1",
            name="Gouvernance de la continuité",
            start=parser.parse("2026-10-12T09:00:00+02:00"),
            end=parser.parse("2026-10-12T13:00:00+02:00"),
            room="T 110",
            teacher="FERNANDEZ VALLE",
        )
    ]
    with patch("web.routes_api.get_week_schedule", new=AsyncMock(return_value=mock_courses)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/schedule/week?date=2026-10-12&url=https://example.com/cal.ics"
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 5  # Mon..Fri
            assert len(data[0]) == 1  # Monday has 1 event
            assert data[0][0]["name"] == "Gouvernance de la continuité"
            assert data[0][0]["teacher"] == "FERNANDEZ VALLE"


@pytest.mark.asyncio
async def test_auth_callback_and_settings_flow():
    app = create_web_app()
    fake_token = {"access_token": "mock_token_123"}
    fake_user = {
        "id": "123456789012345678",
        "username": "testuser",
        "global_name": "Test User",
        "avatar": "avatar_hash",
    }

    class MockResponse:
        def __init__(self, status, json_data):
            self.status = status
            self._json = json_data

        async def json(self):
            return self._json

        async def text(self):
            return ""

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockSession:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def post(self, url, **kwargs):
            return MockResponse(200, fake_token)

        def get(self, url, **kwargs):
            return MockResponse(200, fake_user)

    with (
        patch("web.routes_auth.aiohttp.ClientSession", MockSession),
        patch("config.settings.discord_client_id", "test_client_id"),
        patch("config.settings.discord_client_secret", "test_client_secret"),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Trigger callback
            resp_cb = await client.get("/auth/callback?code=mock_code")
            assert resp_cb.status_code in (302, 303, 307)

            # 2. Check /api/me
            resp_me = await client.get("/api/me")
            assert resp_me.status_code == 200
            me_data = resp_me.json()
            assert me_data["logged_in"] is True
            assert me_data["user"]["discord_id"] == 123456789012345678

            # 3. Update settings
            resp_settings = await client.post(
                "/api/settings",
                json={
                    "ical_url": "https://example.com/user_cal.ics",
                    "daily_notifications": True,
                    "weekly_notifications": True,
                    "prefer_image": False,
                    "language": "en",
                },
            )
            assert resp_settings.status_code == 200
            settings_data = resp_settings.json()
            assert settings_data["settings"]["ical_url"] == "https://example.com/user_cal.ics"
            assert settings_data["settings"]["daily_notifications"] is True
            assert settings_data["settings"]["weekly_notifications"] is True
            assert settings_data["settings"]["prefer_image"] is False
            assert settings_data["settings"]["language"] == "en"

            # Check /api/me reflects new language
            resp_me_after = await client.get("/api/me")
            assert resp_me_after.json()["settings"]["language"] == "en"

            # 4. Check schedule without url param (uses DB ical_url)
            with patch("web.routes_api.get_week_schedule", new=AsyncMock(return_value=[])):
                resp_sched = await client.get("/api/schedule/week?date=2026-10-12")
                assert resp_sched.status_code == 200
