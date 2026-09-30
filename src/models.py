"""Data models for schedule events and user configuration."""

from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import BaseModel
from sqlalchemy import BigInteger
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


def get_utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(UTC)


class CourseEvent(BaseModel):
    """Represents a scheduled course or event parsed from iCal."""

    uid: str
    name: str
    start: datetime
    end: datetime
    room: str | None = None
    teacher: str | None = None
    group: str | None = None
    description: str | None = None
    teams_link: str | None = None
    event_type: str = "course"  # "course", "holiday", "work"

    @property
    def event_date(self) -> date:
        return self.start.date()

    @property
    def time_range_str(self) -> str:
        return f"{self.start.strftime('%H:%M')} - {self.end.strftime('%H:%M')}"

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)


class UserProfile(SQLModel, table=True):
    """Database model for registered Discord users and settings."""

    __tablename__ = "users"

    discord_id: int = SQLField(
        primary_key=True,
        sa_type=BigInteger,
        description="Discord user 64-bit ID",
    )
    ical_url: str | None = SQLField(default=None, description="Direct Hyperplanning iCal URL")
    daily_notifications: bool = SQLField(default=False, description="Send daily schedule at 06:00")
    weekly_notifications: bool = SQLField(
        default=False, description="Send weekly schedule on Monday at 06:00"
    )
    prefer_image: bool = SQLField(
        default=True, description="Render schedules as image cards by default"
    )
    language: str = SQLField(default="fr", description="Language preference ('fr' or 'en')")
    show_work_days: bool = SQLField(
        default=True, description="Display synthetic work/alternance on class-free weekdays"
    )
    updated_at: datetime = SQLField(
        default_factory=get_utc_now, description="Last update timestamp"
    )
