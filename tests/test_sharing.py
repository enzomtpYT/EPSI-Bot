"""Unit and integration tests for schedule sharing, whitelist access control, and timezones."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient

from database import (
    add_whitelisted_viewer,
    generate_or_get_share_token,
    get_schedules_shared_with,
    get_user_by_share_token,
    get_user_profile,
    get_whitelisted_viewers,
    init_db,
    is_user_authorized_to_view,
    register_user_ical,
    remove_whitelisted_viewer,
    set_database_url,
    toggle_sharing,
    update_user_full_settings,
)
from models import CourseEvent
from services.ical_service import convert_course_timezone, get_timezone_safely
from web.app import create_web_app


@pytest.fixture(autouse=True)
async def setup_test_db():
    set_database_url("sqlite+aiosqlite:///:memory:")
    await init_db()


def make_mock_oauth_session(user_id: int, username: str = "TestUser") -> Any:
    fake_token = {"access_token": "mock_token_123"}
    fake_user = {
        "id": str(user_id),
        "username": username,
        "global_name": username,
        "avatar": "avatar_hash",
    }

    class MockResponse:
        def __init__(self, status: int, json_data: dict[str, Any]):
            self.status = status
            self._json = json_data

        async def json(self) -> dict[str, Any]:
            return self._json

        async def text(self) -> str:
            return ""

        async def __aenter__(self) -> MockResponse:
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

    class MockSession:
        def __init__(self, *args: Any, **kwargs: Any):
            pass

        async def __aenter__(self) -> MockSession:
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        def post(self, url: str, **kwargs: Any) -> MockResponse:
            return MockResponse(200, fake_token)

        def get(self, url: str, **kwargs: Any) -> MockResponse:
            return MockResponse(200, fake_user)

    return MockSession


async def login_client(client: AsyncClient, user_id: int, username: str = "TestUser") -> None:
    mock_session = make_mock_oauth_session(user_id, username)
    with (
        patch("web.routes_auth.aiohttp.ClientSession", mock_session),
        patch("config.settings.discord_client_id", "test_id"),
        patch("config.settings.discord_client_secret", "test_secret"),
    ):
        resp = await client.get(f"/auth/callback?code=code_{user_id}")
        assert resp.status_code in (302, 303, 307)


@pytest.mark.asyncio
async def test_database_sharing_and_whitelist_crud() -> None:
    owner_id = 111111
    viewer_a = 222222
    viewer_b = 333333

    # Register owner and viewer profiles
    await register_user_ical(owner_id, "https://example.com/owner.ics")
    await register_user_ical(viewer_a, "https://example.com/viewer_a.ics")

    # Initial state: sharing is disabled by default
    owner = await get_user_profile(owner_id)
    assert owner is not None
    assert owner.share_enabled is False
    assert owner.timezone == "Europe/Paris"

    # Whitelist is initially empty
    viewers = await get_whitelisted_viewers(owner_id)
    assert viewers == []

    # Add viewers to whitelist
    assert await add_whitelisted_viewer(owner_id, viewer_a) is True
    assert await add_whitelisted_viewer(owner_id, viewer_b) is True
    # Duplicate add should return False since already present
    assert await add_whitelisted_viewer(owner_id, viewer_a) is False

    viewers = await get_whitelisted_viewers(owner_id)
    assert viewer_a in viewers
    assert viewer_b in viewers

    # Check authorization when share_enabled is False
    assert await is_user_authorized_to_view(owner_id, viewer_a) is False

    # Enable sharing
    toggle_res = await toggle_sharing(owner_id, True)
    assert toggle_res is not None and toggle_res.share_enabled is True
    owner = await get_user_profile(owner_id)
    assert owner is not None and owner.share_enabled is True

    # Now viewer_a is authorized, but random viewer_c is not
    assert await is_user_authorized_to_view(owner_id, viewer_a) is True
    assert await is_user_authorized_to_view(owner_id, 999999) is False

    # Check reverse query: schedules shared with viewer_a
    shared_with_a = await get_schedules_shared_with(viewer_a)
    assert len(shared_with_a) == 1
    assert shared_with_a[0].discord_id == owner_id

    # Remove viewer_b from whitelist
    assert await remove_whitelisted_viewer(owner_id, viewer_b) is True
    viewers = await get_whitelisted_viewers(owner_id)
    assert viewer_b not in viewers
    assert viewer_a in viewers

    # Token generation and lookup
    token = await generate_or_get_share_token(owner_id)
    assert token is not None and len(token) > 10
    # Same token returned if requested again without force
    token2 = await generate_or_get_share_token(owner_id)
    assert token == token2

    # Lookup user by share token
    user_by_token = await get_user_by_share_token(token)
    assert user_by_token is not None
    assert user_by_token.discord_id == owner_id

    # Regenerate token
    new_token = await generate_or_get_share_token(owner_id, force_new=True)
    assert new_token != token
    assert await get_user_by_share_token(token) is None
    assert await get_user_by_share_token(new_token) is not None

    # Update full settings with custom timezone
    await update_user_full_settings(
        owner_id,
        daily_notifications=True,
        weekly_notifications=True,
        prefer_image=False,
        language="en",
        show_work_days=False,
        timezone="America/New_York",
        share_enabled=True,
    )
    owner = await get_user_profile(owner_id)
    assert owner is not None
    assert owner.timezone == "America/New_York"


def test_timezone_conversion_helpers() -> None:
    # 1. get_timezone_safely
    tz_ny = get_timezone_safely("America/New_York")
    assert tz_ny.key == "America/New_York"

    tz_invalid = get_timezone_safely("Mars/Curiosity")
    assert tz_invalid.key == "Europe/Paris"

    # 2. convert_course_timezone
    # 2026-10-12 09:00 to 13:00 Europe/Paris (UTC+2 in October)
    paris_tz = ZoneInfo("Europe/Paris")
    start_dt = datetime(2026, 10, 12, 9, 0, tzinfo=paris_tz)
    end_dt = datetime(2026, 10, 12, 13, 0, tzinfo=paris_tz)

    course = CourseEvent(
        uid="course-test-1",
        name="Algorithmique",
        start=start_dt,
        end=end_dt,
        room="Amphi A",
        teacher="Professeur Tournesol",
    )

    # Convert to America/New_York (EDT = UTC-4 in October, difference is 6 hours)
    converted = convert_course_timezone(course, "America/New_York")
    assert converted.start.tzinfo is not None
    assert converted.start.hour == 3  # 09:00 Paris -> 03:00 NY
    assert converted.start.minute == 0
    assert converted.end.hour == 7  # 13:00 Paris -> 07:00 NY
    assert course.start.strftime("%H:%M") == "09:00"
    assert course.end.strftime("%H:%M") == "13:00"


@pytest.mark.asyncio
async def test_web_sharing_api_endpoints() -> None:
    app = create_web_app()

    owner_id = 555001
    viewer_id = 555002

    await register_user_ical(owner_id, "https://example.com/owner.ics")
    await register_user_ical(viewer_id, "https://example.com/viewer.ics")
    await toggle_sharing(owner_id, True)
    token = await generate_or_get_share_token(owner_id)

    mock_courses = [
        CourseEvent(
            uid="event-share-1",
            name="Architecture Réseau",
            start=datetime(2026, 10, 12, 9, 0, tzinfo=ZoneInfo("Europe/Paris")),
            end=datetime(2026, 10, 12, 12, 30, tzinfo=ZoneInfo("Europe/Paris")),
            room="Lab 3",
            teacher="M. Smith",
        )
    ]

    with patch("web.routes_api.get_week_schedule", new=AsyncMock(return_value=mock_courses)):
        # Client 1: Unauthenticated visitor / public share link
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as anon_client:
            # 1. Access schedule via share token with timezone conversion
            resp = await anon_client.get(
                f"/api/schedule/week?date=2026-10-12&token={token}&tz=America/New_York"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 5
            day_monday = data[0]
            assert len(day_monday) >= 1
            first_event = day_monday[0]
            assert first_event["name"] == "Architecture Réseau"
            assert first_event["start_time"] == "03:00"
            assert first_event["end_time"] == "06:30"
            assert first_event["school_start_time"] == "09:00"
            assert first_event["school_end_time"] == "12:30"

            # 2. Access with invalid token should be 403
            resp_bad_token = await anon_client.get(
                "/api/schedule/week?date=2026-10-12&token=invalidtoken123"
            )
            assert resp_bad_token.status_code == 403

            # 3. Share HTML route (/share/{token})
            resp_share_page = await anon_client.get(f"/share/{token}")
            assert resp_share_page.status_code == 200
            assert "EPSI Emploi du temps" in resp_share_page.text

        # Client 2: Owner client (authenticated)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as owner_client:
            await login_client(owner_client, owner_id, "OwnerUser")

            # Get whitelist
            resp_wl = await owner_client.get("/api/share/whitelist")
            assert resp_wl.status_code == 200
            assert resp_wl.json()["viewers"] == []

            # Add viewer_id to whitelist (supports string and int)
            resp_add = await owner_client.post(
                "/api/share/whitelist",
                json={"viewer_id": str(viewer_id)},
            )
            assert resp_add.status_code == 200

            resp_wl2 = await owner_client.get("/api/share/whitelist")
            assert resp_wl2.json()["viewers"] == [str(viewer_id)]

            # Test 64-bit Discord snowflake precision (e.g. 1026865713203388447)
            large_snowflake = 1026865713203388447
            resp_add_large = await owner_client.post(
                "/api/share/whitelist",
                json={"viewer_id": str(large_snowflake)},
            )
            assert resp_add_large.status_code == 200
            resp_wl_large = await owner_client.get("/api/share/whitelist")
            assert str(large_snowflake) in resp_wl_large.json()["viewers"]
            # Clean up large snowflake
            resp_del_large = await owner_client.delete(f"/api/share/whitelist/{large_snowflake}")
            assert resp_del_large.status_code == 200

            # Client 3: Viewer client (authenticated)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as viewer_client:
                await login_client(viewer_client, viewer_id, "ViewerUser")

                # Viewer checks /api/shared-with-me
                resp_shared = await viewer_client.get("/api/shared-with-me")
                assert resp_shared.status_code == 200
                shared_list = resp_shared.json()
                assert len(shared_list) == 1
                assert shared_list[0]["discord_id"] == str(owner_id)

                # Viewer accesses owner's schedule via owner_id parameter
                resp_viewer_access = await viewer_client.get(
                    f"/api/schedule/week?date=2026-10-12&owner_id={owner_id}",
                )
                assert resp_viewer_access.status_code == 200

                # Owner deletes viewer from whitelist
                resp_del = await owner_client.delete(f"/api/share/whitelist/{viewer_id}")
                assert resp_del.status_code == 200

                # Now viewer is forbidden
                resp_forbidden = await viewer_client.get(
                    f"/api/schedule/week?date=2026-10-12&owner_id={owner_id}",
                )
                assert resp_forbidden.status_code == 403

            # Regenerate token endpoint
            resp_regen = await owner_client.post("/api/share/token/regenerate")
            assert resp_regen.status_code == 200
            assert resp_regen.json()["token"] != token
