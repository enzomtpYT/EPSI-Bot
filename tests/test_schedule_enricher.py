"""Unit tests for schedule enricher service."""

from datetime import UTC, date, datetime

import pytest

from models import CourseEvent
from services.schedule_enricher import enrich_schedule


@pytest.mark.asyncio
async def test_enrich_schedule_empty_weekday_with_work():
    """Verify empty weekday gets Entreprise event when show_work_days=True."""
    # 2026-10-13 is a Tuesday, not a holiday
    target_date = date(2026, 10, 13)
    enriched = await enrich_schedule(
        courses=[],
        start_date=target_date,
        end_date=target_date,
        show_work_days=True,
        lang="fr",
    )

    assert len(enriched) == 1
    event = enriched[0]
    assert event.event_type == "work"
    assert event.name == "Entreprise"
    assert event.room == "Alternance"
    assert event.start.hour == 9
    assert event.end.hour == 17


@pytest.mark.asyncio
async def test_enrich_schedule_empty_weekday_without_work():
    """Verify empty weekday remains empty when show_work_days=False."""
    target_date = date(2026, 10, 13)
    enriched = await enrich_schedule(
        courses=[],
        start_date=target_date,
        end_date=target_date,
        show_work_days=False,
        lang="fr",
    )

    assert len(enriched) == 0


@pytest.mark.asyncio
async def test_enrich_schedule_holiday():
    """Verify French public holiday generates holiday event and no work event."""
    # 2026-05-01 is a Friday and a French holiday (Fête du Travail)
    holiday_date = date(2026, 5, 1)
    enriched = await enrich_schedule(
        courses=[],
        start_date=holiday_date,
        end_date=holiday_date,
        show_work_days=True,
        lang="fr",
    )

    assert len(enriched) == 1
    event = enriched[0]
    assert event.event_type == "holiday"
    assert event.name == "Fête du Travail"
    assert event.room == "Jour férié"


@pytest.mark.asyncio
async def test_enrich_schedule_weekday_with_courses_not_overwritten():
    """Verify days that already have courses are not replaced with work events."""
    target_date = date(2026, 10, 13)
    existing_course = CourseEvent(
        uid="course-123",
        name="Algorithmique",
        start=datetime(2026, 10, 13, 9, 0, tzinfo=UTC),
        end=datetime(2026, 10, 13, 12, 0, tzinfo=UTC),
        room="Salle 101",
        teacher="M. Dupont",
    )

    enriched = await enrich_schedule(
        courses=[existing_course],
        start_date=target_date,
        end_date=target_date,
        show_work_days=True,
        lang="fr",
    )

    assert len(enriched) == 1
    assert enriched[0].uid == "course-123"
    assert enriched[0].event_type == "course"


@pytest.mark.asyncio
async def test_enrich_schedule_weekend_not_work():
    """Verify weekends (Saturday/Sunday) do not get work events."""
    # 2026-10-17 is Saturday, 2026-10-18 is Sunday
    sat = date(2026, 10, 17)
    sun = date(2026, 10, 18)

    enriched = await enrich_schedule(
        courses=[],
        start_date=sat,
        end_date=sun,
        show_work_days=True,
        lang="fr",
    )

    assert len(enriched) == 0
