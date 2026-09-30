"""Unit tests for iCalendar parsing and event extraction."""

import io
from datetime import date, datetime
from zoneinfo import ZoneInfo

from models import CourseEvent
from services.embed_builder import create_day_embed, create_now_embed, create_week_embed
from services.ical_service import (
    parse_event_details,
    parse_ical_events_in_range,
)
from services.image_renderer import render_day_image, render_week_image

SAMPLE_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EPSI//FR
BEGIN:VEVENT
UID:test-12345
DTSTART:20261015T080000Z
DTEND:20261015T120000Z
SUMMARY:Architecture Logicielle - DUPONT - BAC+4
LOCATION:SALLE 204 (30)
DESCRIPTION:Matière : Architecture Logicielle\\nIntervenant : DUPONT\\nGroupe : BAC+4\\nSalle : SALLE 204 (30)\\nhttps://teams.microsoft.com/l/meetup-join/19%3ameeting_xyz%40thread.v2/0
END:VEVENT
BEGIN:VEVENT
UID:test-67890
DTSTART:20261015T130000Z
DTEND:20261015T170000Z
SUMMARY:DevOps & Cloud - MARTIN - BAC+4
LOCATION:SALLE 101 (25)
DESCRIPTION:Matière : DevOps & Cloud\\nIntervenant : MARTIN\\nGroupe : BAC+4\\nSalle : SALLE 101 (25)
END:VEVENT
END:VCALENDAR"""


def test_parse_event_details() -> None:
    desc = (
        "Matière : Dev Web Avancé\n"
        "Intervenant : TURING Alan\n"
        "Groupe : B3 DEV\n"
        "Salle : AMPHI 1\n"
        "https://teams.microsoft.com/l/meetup-join/meeting-test"
    )
    details = parse_event_details(
        summary="Dev Web Avancé - TURING",
        description=desc,
        location="AMPHI 1",
    )
    assert details["name"] == "Dev Web Avancé"
    assert details["teacher"] == "TURING Alan"
    assert details["room"] == "AMPHI 1"
    assert details["group"] == "B3 DEV"
    assert details["teams_link"] == "https://teams.microsoft.com/l/meetup-join/meeting-test"


def test_parse_ical_events_in_range() -> None:
    tz = ZoneInfo("Europe/Paris")
    start = datetime(2026, 10, 15, 0, 0, tzinfo=tz)
    end = datetime(2026, 10, 15, 23, 59, tzinfo=tz)

    courses = parse_ical_events_in_range(SAMPLE_ICAL, start, end)
    assert len(courses) == 2

    c1 = courses[0]
    assert c1.uid == "test-12345"
    assert c1.name == "Architecture Logicielle"
    assert c1.teacher == "DUPONT"
    assert c1.room == "SALLE 204 (30)"
    assert c1.teams_link is not None
    assert c1.duration_minutes == 240

    c2 = courses[1]
    assert c2.uid == "test-67890"
    assert c2.name == "DevOps & Cloud"
    assert c2.teacher == "MARTIN"


def test_image_renderer_day_and_week() -> None:
    tz = ZoneInfo("Europe/Paris")
    event1 = CourseEvent(
        uid="c1",
        name="Algorithmique",
        start=datetime(2026, 10, 15, 8, 30, tzinfo=tz),
        end=datetime(2026, 10, 15, 12, 30, tzinfo=tz),
        room="B 201",
        teacher="Professeur X",
    )
    event2 = CourseEvent(
        uid="c2",
        name="Base de Données",
        start=datetime(2026, 10, 15, 13, 30, tzinfo=tz),
        end=datetime(2026, 10, 15, 17, 30, tzinfo=tz),
        room="B 202",
        teacher="Professeur Y",
    )

    courses = [event1, event2]
    target_date = date(2026, 10, 15)

    # Test day image generation
    day_buf = render_day_image(target_date, courses)
    assert isinstance(day_buf, io.BytesIO)
    day_bytes = day_buf.getvalue()
    assert len(day_bytes) > 1000
    assert day_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    # Test empty day image generation
    empty_buf = render_day_image(target_date, [])
    assert len(empty_buf.getvalue()) > 1000

    # Test week image generation
    week_start = date(2026, 10, 12)
    week_buf = render_week_image(week_start, courses)
    assert isinstance(week_buf, io.BytesIO)
    week_bytes = week_buf.getvalue()
    assert len(week_bytes) > 1000
    assert week_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_embed_builders() -> None:
    tz = ZoneInfo("Europe/Paris")
    event1 = CourseEvent(
        uid="c1",
        name="Cyber Sécurité",
        start=datetime(2026, 10, 15, 9, 0, tzinfo=tz),
        end=datetime(2026, 10, 15, 12, 0, tzinfo=tz),
        room="Salle Réseau",
        teacher="Expert Sec",
    )
    courses = [event1]

    # Day Embed
    day_embed = create_day_embed(date(2026, 10, 15), courses)
    assert "Cyber Sécurité" in str(day_embed.fields[0].name)
    assert "Salle Réseau" in str(day_embed.fields[0].value)

    # Week Embed
    week_embed = create_week_embed(date(2026, 10, 12), courses)
    assert len(week_embed.fields) > 0

    # Now Embed
    now_embed = create_now_embed(event1, [])
    assert "En cours actuellement" in str(now_embed.fields[0].name)
