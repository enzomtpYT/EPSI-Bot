"""iCalendar fetching, caching, and event parsing logic."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp
import recurring_ical_events
from icalendar import Calendar

from config import settings
from models import CourseEvent

logger = logging.getLogger(__name__)

# In-memory cache for iCal text: url -> (fetch_time, ical_text)
_ICAL_CACHE: dict[str, tuple[datetime, str]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes cache to avoid spamming Hyperplanning servers


def get_local_timezone() -> ZoneInfo:
    """Return configured timezone using standard library ZoneInfo."""
    try:
        return ZoneInfo(settings.timezone)
    except Exception:
        return ZoneInfo("Europe/Paris")


def get_timezone_safely(tz_name: str | None) -> ZoneInfo:
    """Return ZoneInfo for tz_name or fallback to Europe/Paris."""
    if not tz_name:
        return get_local_timezone()
    clean = tz_name.strip()
    try:
        return ZoneInfo(clean)
    except Exception:
        pass
    try:
        return ZoneInfo(clean.replace(" ", "_"))
    except Exception:
        return get_local_timezone()


def convert_course_timezone(course: CourseEvent, target_tz_name: str | None) -> CourseEvent:
    """Return a copy of CourseEvent with start and end converted to target timezone."""
    tz = get_timezone_safely(target_tz_name)
    start_conv = course.start.astimezone(tz)
    end_conv = course.end.astimezone(tz)
    return CourseEvent(
        uid=course.uid,
        name=course.name,
        start=start_conv,
        end=end_conv,
        room=course.room,
        teacher=course.teacher,
        group=course.group,
        description=course.description,
        teams_link=course.teams_link,
        event_type=course.event_type,
    )


def strip_teams_links(courses: Sequence[CourseEvent]) -> list[CourseEvent]:
    """Return a copy of courses with teams_link stripped for privacy in shared views."""
    return [
        CourseEvent(
            uid=c.uid,
            name=c.name,
            start=c.start,
            end=c.end,
            room=c.room,
            teacher=c.teacher,
            group=c.group,
            description=c.description,
            teams_link=None,
            event_type=c.event_type,
        )
        for c in courses
    ]


def parse_event_details(summary: str, description: str, location: str) -> dict[str, str | None]:
    """Extract course name, teacher, room, and teams links from Hyperplanning fields."""
    details: dict[str, str | None] = {
        "name": summary.strip() if summary else "Cours",
        "teacher": None,
        "room": location.strip() if location else None,
        "group": None,
        "teams_link": None,
    }

    if description:
        # Match "Matière : <val>"
        m_mat = re.search(r"Mati[èe]re\s*:\s*([^\n\r]+)", description, re.IGNORECASE)
        if m_mat:
            details["name"] = m_mat.group(1).strip()

        # Match "Intervenant : <val>"
        m_prof = re.search(r"Intervenant\s*:\s*([^\n\r]+)", description, re.IGNORECASE)
        if m_prof:
            details["teacher"] = m_prof.group(1).strip()

        # Match "Salle : <val>" or "Salles : <val>"
        m_room = re.search(r"Salles?\s*:\s*([^\n\r]+)", description, re.IGNORECASE)
        if m_room and not details["room"]:
            details["room"] = m_room.group(1).strip()

        # Match "Groupe : <val>"
        m_grp = re.search(r"Groupe\s*:\s*([^\n\r]+)", description, re.IGNORECASE)
        if m_grp:
            details["group"] = m_grp.group(1).strip()

        # Extract Teams meeting link if present
        m_teams = re.search(r"https://teams\.microsoft\.com/l/meetup-join/[^\s\"<>]+", description)
        if m_teams:
            details["teams_link"] = m_teams.group(0)

    # Fallback for teacher: Hyperplanning summaries are usually:
    # "Subject - TEACHER - Group" or "Subject - TEACHER"
    if not details["teacher"] and summary:
        parts = [p.strip() for p in summary.split(" - ") if p.strip()]
        if len(parts) >= 2:
            # The second component is typically the teacher/intervenant
            details["teacher"] = parts[1]

    # Clean up escaping in room if any (like \,)
    if details["room"]:
        details["room"] = details["room"].replace(r"\,", ",").strip()

    return details


def parse_ical_events_in_range(
    ical_content: str,
    start_dt: datetime,
    end_dt: datetime,
) -> list[CourseEvent]:
    """Parse iCal text and return sorted CourseEvents between start_dt and end_dt."""
    tz = get_local_timezone()

    # Ensure search dates are timezone-aware in local timezone
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tz)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tz)

    calendar = Calendar.from_ical(ical_content)
    events = recurring_ical_events.of(calendar).between(start_dt, end_dt)

    parsed_courses: list[CourseEvent] = []

    for event in events:
        uid = str(event.get("UID", ""))
        summary = str(event.get("SUMMARY", ""))
        desc = str(event.get("DESCRIPTION", ""))
        location = str(event.get("LOCATION", ""))

        dtstart = event.get("DTSTART").dt
        dtend = event.get("DTEND").dt

        # Normalize start datetime
        if isinstance(dtstart, datetime):
            if dtstart.tzinfo is None:
                start_local = dtstart.replace(tzinfo=tz)
            else:
                start_local = dtstart.astimezone(tz)
        else:
            # Whole-day event
            start_local = datetime.combine(dtstart, datetime.min.time(), tzinfo=tz)

        # Normalize end datetime
        if isinstance(dtend, datetime):
            if dtend.tzinfo is None:
                end_local = dtend.replace(tzinfo=tz)
            else:
                end_local = dtend.astimezone(tz)
        else:
            end_local = datetime.combine(dtend, datetime.min.time(), tzinfo=tz)

        details = parse_event_details(summary, desc, location)

        parsed_courses.append(
            CourseEvent(
                uid=uid,
                name=details["name"] or "Cours",
                start=start_local,
                end=end_local,
                room=details["room"],
                teacher=details["teacher"],
                group=details["group"],
                description=desc if desc else None,
                teams_link=details["teams_link"],
            )
        )

    # Sort courses chronologically
    parsed_courses.sort(key=lambda c: c.start)
    return parsed_courses


async def fetch_ical_content(url: str, force_refresh: bool = False) -> str:
    """Fetch raw iCal content with caching and timeout handling."""
    now = datetime.now(UTC)

    if not force_refresh and url in _ICAL_CACHE:
        cached_time, cached_content = _ICAL_CACHE[url]
        if (now - cached_time).total_seconds() < CACHE_TTL_SECONDS:
            logger.info("Serving iCal from in-memory cache.")
            return cached_content

    logger.info("Fetching iCal content from source...")
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"Failed to fetch iCal (HTTP {response.status})")
            text = await response.text(encoding="utf-8")
            _ICAL_CACHE[url] = (now, text)
            return text


async def get_day_schedule(
    url: str,
    target_date: date | None = None,
    force_refresh: bool = False,
) -> list[CourseEvent]:
    """Get all scheduled courses for a specific day."""
    tz = get_local_timezone()
    if target_date is None:
        target_date = datetime.now(tz).date()

    start_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=tz)
    end_dt = start_dt + timedelta(days=1)

    ical_text = await fetch_ical_content(url, force_refresh=force_refresh)
    return parse_ical_events_in_range(ical_text, start_dt, end_dt)


async def get_week_schedule(
    url: str,
    target_date: date | None = None,
    force_refresh: bool = False,
) -> list[CourseEvent]:
    """Get all scheduled courses for the week (Monday through Sunday) containing target_date."""
    tz = get_local_timezone()
    if target_date is None:
        target_date = datetime.now(tz).date()

    # Monday of current week
    start_of_week = target_date - timedelta(days=target_date.weekday())
    start_dt = datetime.combine(start_of_week, datetime.min.time(), tzinfo=tz)
    end_dt = start_dt + timedelta(days=7)

    ical_text = await fetch_ical_content(url, force_refresh=force_refresh)
    return parse_ical_events_in_range(ical_text, start_dt, end_dt)


async def get_next_classes(
    url: str,
    limit: int = 3,
    force_refresh: bool = False,
) -> tuple[CourseEvent | None, list[CourseEvent]]:
    """Return currently running class (if any) and upcoming classes."""
    tz = get_local_timezone()
    now_dt = datetime.now(tz)
    end_dt = now_dt + timedelta(days=5)

    ical_text = await fetch_ical_content(url, force_refresh=force_refresh)
    courses = parse_ical_events_in_range(ical_text, now_dt - timedelta(hours=4), end_dt)

    current_class: CourseEvent | None = None
    upcoming_classes: list[CourseEvent] = []

    for course in courses:
        if course.start <= now_dt < course.end:
            current_class = course
        elif course.start > now_dt and len(upcoming_classes) < limit:
            upcoming_classes.append(course)

    return current_class, upcoming_classes
