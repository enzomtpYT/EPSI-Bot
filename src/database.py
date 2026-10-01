"""Database setup and async operations for user profiles."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, col, select

from config import settings
from models import UserProfile, UserShareWhitelist

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def set_database_url(url: str) -> None:
    """Reconfigure engine and session maker with a custom database URL (e.g. for testing)."""
    global engine, async_session_maker
    engine = create_async_engine(url, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )


async def _run_alter_queries(conn) -> None:
    """Safely apply column additions for PostgreSQL or SQLite."""
    queries = [
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'fr';",
            "ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'fr';",
        ),
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS show_work_days BOOLEAN DEFAULT TRUE;",
            "ALTER TABLE users ADD COLUMN show_work_days BOOLEAN DEFAULT 1;",
        ),
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Europe/Paris';",
            "ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Paris';",
        ),
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS share_enabled BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE users ADD COLUMN share_enabled BOOLEAN DEFAULT 0;",
        ),
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS share_token VARCHAR(64) DEFAULT NULL;",
            "ALTER TABLE users ADD COLUMN share_token VARCHAR(64) DEFAULT NULL;",
        ),
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(100) DEFAULT NULL;",
            "ALTER TABLE users ADD COLUMN display_name VARCHAR(100) DEFAULT NULL;",
        ),
        (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255) DEFAULT NULL;",
            "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255) DEFAULT NULL;",
        ),
    ]
    for pg_sql, sqlite_sql in queries:
        try:
            await conn.execute(text(pg_sql))
        except Exception:
            try:
                await conn.execute(text(sqlite_sql))
            except Exception:
                pass


async def init_db() -> None:
    """Initialize database tables, falling back to SQLite if PostgreSQL fails."""
    logger.info("Initializing database schema...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            await _run_alter_queries(conn)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        if "postgresql" in settings.database_url:
            logger.warning(
                f"Failed to connect to PostgreSQL ({e}). Falling back to local SQLite database..."
            )
            set_database_url(settings.sqlite_database_url)
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
                await _run_alter_queries(conn)
            logger.info("Database initialized successfully with SQLite fallback.")
        else:
            raise


async def get_user_profile(discord_id: int) -> UserProfile | None:
    """Retrieve user profile by Discord ID."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()


async def register_user_ical(discord_id: int, ical_url: str) -> UserProfile:
    """Register or update a user's iCal URL."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if user:
            user.ical_url = ical_url
            user.updated_at = now
        else:
            user = UserProfile(discord_id=discord_id, ical_url=ical_url, updated_at=now)
            session.add(user)

        await session.commit()
        await session.refresh(user)
        return user


async def delete_user_profile(discord_id: int) -> bool:
    """Delete a user profile and their registered iCal."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False


async def update_user_notifications(
    discord_id: int,
    *,
    daily: bool | None = None,
    weekly: bool | None = None,
    prefer_image: bool | None = None,
    language: str | None = None,
    show_work_days: bool | None = None,
) -> UserProfile | None:
    """Update notification preferences for a user."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None

        if daily is not None:
            user.daily_notifications = daily
        if weekly is not None:
            user.weekly_notifications = weekly
        if prefer_image is not None:
            user.prefer_image = prefer_image
        if language is not None:
            user.language = language
        if show_work_days is not None:
            user.show_work_days = show_work_days

        user.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(user)
        return user


async def get_or_create_user_profile(
    discord_id: int,
    *,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> UserProfile:
    """Retrieve or create user profile by Discord ID, updating display_name/avatar if provided."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            user = UserProfile(
                discord_id=discord_id,
                display_name=display_name,
                avatar_url=avatar_url,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            changed = False
            if display_name is not None and user.display_name != display_name:
                user.display_name = display_name
                changed = True
            if avatar_url is not None and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
                changed = True
            if changed:
                user.updated_at = datetime.now(UTC)
                await session.commit()
                await session.refresh(user)
        return user


async def update_user_full_settings(
    discord_id: int,
    *,
    ical_url: str | None = None,
    daily_notifications: bool | None = None,
    weekly_notifications: bool | None = None,
    prefer_image: bool | None = None,
    language: str | None = None,
    show_work_days: bool | None = None,
    timezone: str | None = None,
    share_enabled: bool | None = None,
    share_token: str | None = None,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> UserProfile:
    """Update complete user profile settings, creating profile if not exists."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if not user:
            user = UserProfile(
                discord_id=discord_id,
                ical_url=ical_url.strip() if (ical_url and ical_url.strip()) else None,
                daily_notifications=daily_notifications
                if daily_notifications is not None
                else False,
                weekly_notifications=weekly_notifications
                if weekly_notifications is not None
                else False,
                prefer_image=prefer_image if prefer_image is not None else True,
                language=language if language is not None else "fr",
                show_work_days=show_work_days if show_work_days is not None else True,
                timezone=timezone if timezone is not None else "Europe/Paris",
                share_enabled=share_enabled if share_enabled is not None else False,
                share_token=share_token,
                display_name=display_name,
                avatar_url=avatar_url,
                updated_at=now,
            )
            session.add(user)
        else:
            if ical_url is not None:
                user.ical_url = ical_url.strip() if ical_url.strip() else None
            if daily_notifications is not None:
                user.daily_notifications = daily_notifications
            if weekly_notifications is not None:
                user.weekly_notifications = weekly_notifications
            if prefer_image is not None:
                user.prefer_image = prefer_image
            if language is not None:
                user.language = language
            if show_work_days is not None:
                user.show_work_days = show_work_days
            if timezone is not None:
                user.timezone = timezone
            if share_enabled is not None:
                user.share_enabled = share_enabled
            if share_token is not None:
                user.share_token = share_token
            if display_name is not None:
                user.display_name = display_name
            if avatar_url is not None:
                user.avatar_url = avatar_url
            user.updated_at = now

        await session.commit()
        await session.refresh(user)
        return user


async def add_whitelisted_viewer(owner_id: int, viewer_id: int) -> bool:
    """Add a viewer Discord ID to the owner's schedule whitelist."""
    if owner_id == viewer_id:
        return True
    async with async_session_maker() as session:
        # Check if already whitelisted
        stmt = select(UserShareWhitelist).where(
            UserShareWhitelist.owner_id == owner_id,
            UserShareWhitelist.viewer_id == viewer_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return False

        entry = UserShareWhitelist(owner_id=owner_id, viewer_id=viewer_id)
        session.add(entry)
        await session.commit()
        return True


async def remove_whitelisted_viewer(owner_id: int, viewer_id: int) -> bool:
    """Remove a viewer Discord ID from the owner's schedule whitelist."""
    async with async_session_maker() as session:
        stmt = select(UserShareWhitelist).where(
            UserShareWhitelist.owner_id == owner_id,
            UserShareWhitelist.viewer_id == viewer_id,
        )
        entry = (await session.execute(stmt)).scalar_one_or_none()
        if not entry:
            return False
        await session.delete(entry)
        await session.commit()
        return True


async def get_whitelisted_viewers(owner_id: int) -> list[int]:
    """Retrieve all Discord IDs whitelisted by an owner."""
    async with async_session_maker() as session:
        stmt = select(UserShareWhitelist.viewer_id).where(UserShareWhitelist.owner_id == owner_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_schedules_shared_with(viewer_id: int) -> Sequence[UserProfile]:
    """Retrieve all owner UserProfiles who have shared their schedule with this viewer."""
    async with async_session_maker() as session:
        share_stmt = select(UserShareWhitelist.owner_id).where(
            UserShareWhitelist.viewer_id == viewer_id
        )
        owner_ids = (await session.execute(share_stmt)).scalars().all()
        if not owner_ids:
            return []
        users_stmt = select(UserProfile).where(
            col(UserProfile.discord_id).in_(owner_ids),
            col(UserProfile.share_enabled).is_(True),
            col(UserProfile.ical_url).isnot(None),
        )
        result = await session.execute(users_stmt)
        return result.scalars().all()


async def is_user_authorized_to_view(owner_id: int, viewer_id: int) -> bool:
    """Check if viewer_id is authorized to view owner_id's schedule."""
    if owner_id == viewer_id:
        return True
    async with async_session_maker() as session:
        owner_stmt = select(UserProfile).where(UserProfile.discord_id == owner_id)
        owner = (await session.execute(owner_stmt)).scalar_one_or_none()
        if not owner or not owner.share_enabled:
            return False

        share_stmt = select(UserShareWhitelist).where(
            UserShareWhitelist.owner_id == owner_id,
            UserShareWhitelist.viewer_id == viewer_id,
        )
        share = (await session.execute(share_stmt)).scalar_one_or_none()
        return share is not None


async def generate_or_get_share_token(owner_id: int, force_new: bool = False) -> str:
    """Get or generate a secret URL-safe share token for web sharing."""
    import secrets

    async with async_session_maker() as session:
        stmt = select(UserProfile).where(UserProfile.discord_id == owner_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        now = datetime.now(UTC)
        if not user:
            user = UserProfile(
                discord_id=owner_id,
                share_enabled=True,
                share_token=secrets.token_urlsafe(24),
                updated_at=now,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user.share_token or ""

        if force_new or not user.share_token:
            user.share_token = secrets.token_urlsafe(24)
            user.share_enabled = True
            user.updated_at = now
            await session.commit()
            await session.refresh(user)
        return user.share_token or ""


async def get_user_by_share_token(token: str) -> UserProfile | None:
    """Look up a user profile by secret web share token."""
    clean = token.strip()
    if not clean:
        return None
    async with async_session_maker() as session:
        stmt = select(UserProfile).where(
            UserProfile.share_token == clean,
            col(UserProfile.share_enabled).is_(True),
        )
        return (await session.execute(stmt)).scalar_one_or_none()


async def toggle_sharing(owner_id: int, enabled: bool) -> UserProfile:
    """Enable or disable schedule sharing for an owner."""
    async with async_session_maker() as session:
        stmt = select(UserProfile).where(UserProfile.discord_id == owner_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        now = datetime.now(UTC)
        if not user:
            user = UserProfile(discord_id=owner_id, share_enabled=enabled, updated_at=now)
            session.add(user)
        else:
            user.share_enabled = enabled
            user.updated_at = now
        await session.commit()
        await session.refresh(user)
        return user


async def get_users_for_daily_notifications() -> Sequence[UserProfile]:
    """Fetch all users who have daily notifications enabled and a valid ical_url."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(
            col(UserProfile.daily_notifications).is_(True),
            col(UserProfile.ical_url).isnot(None),
        )
        result = await session.execute(statement)
        return result.scalars().all()


async def get_users_for_weekly_notifications() -> Sequence[UserProfile]:
    """Fetch all users who have weekly notifications enabled and a valid ical_url."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(
            col(UserProfile.weekly_notifications).is_(True),
            col(UserProfile.ical_url).isnot(None),
        )
        result = await session.execute(statement)
        return result.scalars().all()
