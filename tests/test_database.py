"""Unit tests for database and user profile repository."""

import pytest

from database import (
    delete_user_profile,
    get_user_profile,
    get_users_for_daily_notifications,
    get_users_for_weekly_notifications,
    init_db,
    register_user_ical,
    set_database_url,
    update_user_notifications,
)


@pytest.mark.asyncio
async def test_database_crud_lifecycle() -> None:
    # 0. Configure test database to in-memory sqlite
    set_database_url("sqlite+aiosqlite:///:memory:")

    # 1. Initialize schema
    await init_db()

    test_user_id = 999123456
    ical_url = "https://example.com/test.ics"

    # Ensure clean state
    await delete_user_profile(test_user_id)
    profile = await get_user_profile(test_user_id)
    assert profile is None

    # 2. Register user
    created = await register_user_ical(test_user_id, ical_url)
    assert created.discord_id == test_user_id
    assert created.ical_url == ical_url
    assert created.daily_notifications is False
    assert created.prefer_image is True

    # 3. Retrieve user
    fetched = await get_user_profile(test_user_id)
    assert fetched is not None
    assert fetched.discord_id == test_user_id

    # 4. Update notification preferences and language
    updated = await update_user_notifications(
        test_user_id,
        daily=True,
        weekly=True,
        prefer_image=False,
        language="en",
    )
    assert updated is not None
    assert updated.daily_notifications is True
    assert updated.weekly_notifications is True
    assert updated.prefer_image is False
    assert updated.language == "en"

    # 5. Check notification subscriber queries
    daily_users = await get_users_for_daily_notifications()
    assert any(u.discord_id == test_user_id for u in daily_users)

    weekly_users = await get_users_for_weekly_notifications()
    assert any(u.discord_id == test_user_id for u in weekly_users)

    # 6. Delete user
    deleted = await delete_user_profile(test_user_id)
    assert deleted is True
    assert await get_user_profile(test_user_id) is None
