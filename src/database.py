"""Database setup and async operations for user profiles."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, col, select

from config import settings
from models import UserProfile

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


async def init_db() -> None:
    """Initialize database tables, falling back to SQLite if PostgreSQL fails."""
    logger.info("Initializing database schema...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        if "postgresql" in settings.database_url:
            logger.warning(
                f"Failed to connect to PostgreSQL ({e}). Falling back to local SQLite database..."
            )
            set_database_url(settings.sqlite_database_url)
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
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

        user.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(user)
        return user


async def get_or_create_user_profile(discord_id: int) -> UserProfile:
    """Retrieve or create user profile by Discord ID."""
    async with async_session_maker() as session:
        statement = select(UserProfile).where(UserProfile.discord_id == discord_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            user = UserProfile(discord_id=discord_id)
            session.add(user)
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
