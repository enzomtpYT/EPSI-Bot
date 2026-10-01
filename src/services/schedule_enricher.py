"""Enriches parsed schedule with national holidays and synthetic work/alternance events."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

from models import CourseEvent
from services.holidays import get_french_public_holidays
from services.ical_service import get_local_timezone


async def enrich_schedule(
    courses: Sequence[CourseEvent],
    start_date: date,
    end_date: date,
    show_work_days: bool = True,
    lang: str = "fr",
) -> list[CourseEvent]:
    """Enrich course events with French public holidays and synthetic work events.

    - French public holidays are injected as whole-day events (08:00 - 18:00).
    - If show_work_days is True, any Monday-Friday without scheduled classes and
      not falling on a public holiday receives a synthetic 'Entreprise' event (09:00 - 17:00).
    """
    tz = get_local_timezone()

    # Collect holidays for all relevant years
    years = {start_date.year, end_date.year}
    holidays: dict[date, str] = {}
    for y in years:
        y_holidays = await get_french_public_holidays(y, lang=lang)
        holidays.update(y_holidays)

    # Group existing courses by date (exclude synthetic events if any)
    courses_by_date: dict[date, list[CourseEvent]] = {}
    enriched: list[CourseEvent] = []

    for c in courses:
        # Ignore synthetic events if schedule was already enriched
        if c.uid.startswith("holiday-") or c.uid.startswith("work-"):
            continue

        # If it's a holiday from iCal on a day covered by statutory holidays,
        # skip it so the statutory holiday with canonical name and hours is used instead
        if (
            c.event_type == "holiday" or c.name.strip().lower() in ("férié", "ferie")
        ) and c.event_date in holidays:
            continue

        if c.event_type not in ("holiday", "work"):
            courses_by_date.setdefault(c.event_date, []).append(c)
        enriched.append(c)

    # Iterate over all days in the range
    curr = start_date
    while curr <= end_date:
        if curr in holidays:
            holiday_name = holidays[curr]
            h_start = datetime.combine(curr, time(8, 0), tzinfo=tz)
            h_end = datetime.combine(curr, time(18, 0), tzinfo=tz)
            room_text = "Jour férié" if lang == "fr" else "Public Holiday"

            enriched.append(
                CourseEvent(
                    uid=f"holiday-{curr.isoformat()}",
                    name=holiday_name,
                    start=h_start,
                    end=h_end,
                    room=room_text,
                    teacher=None,
                    group=None,
                    description=f"Jour férié national ({holiday_name})",
                    event_type="holiday",
                )
            )
        elif show_work_days and curr.weekday() < 5 and len(courses_by_date.get(curr, [])) == 0:
            # Weekday (Mon-Fri) with no school courses and not a public holiday
            w_start = datetime.combine(curr, time(9, 0), tzinfo=tz)
            w_end = datetime.combine(curr, time(17, 0), tzinfo=tz)
            work_name = "Entreprise" if lang == "fr" else "Company"
            work_room = "Alternance" if lang == "fr" else "Apprenticeship"

            enriched.append(
                CourseEvent(
                    uid=f"work-{curr.isoformat()}",
                    name=work_name,
                    start=w_start,
                    end=w_end,
                    room=work_room,
                    teacher=None,
                    group=None,
                    description="Journée en entreprise (Alternance)",
                    event_type="work",
                )
            )

        curr += timedelta(days=1)

    # Sort all events chronologically
    enriched.sort(key=lambda c: (c.start, c.end))
    return enriched
