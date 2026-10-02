"""Unit tests for internationalization, localized embeds, and image rendering."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock

from models import CourseEvent, UserProfile
from services.embed_builder import create_day_embed, create_now_embed, create_week_embed
from services.i18n import (
    format_date_localized,
    get_short_day_names,
    resolve_user_language,
    t,
)
from services.image_renderer import render_day_image, render_week_image


def test_i18n_translation_keys():
    assert t("no_classes_day", lang="fr") == "Aucun cours prévu pour cette journée."
    assert t("no_classes_day", lang="en") == "No classes scheduled for this day."
    assert t("room", lang="fr") == "Salle"
    assert t("room", lang="en") == "Room"
    assert t("schedule_week_title", lang="fr", week=42) == "📆 Emploi du temps — Semaine 42"
    assert t("schedule_week_title", lang="en", week=42) == "📆 Schedule — Week 42"


def test_format_date_localized():
    d = date(2026, 10, 12)  # Monday
    fr_date = format_date_localized(d, lang="fr")
    en_date = format_date_localized(d, lang="en")

    assert "Lundi" in fr_date
    assert "octobre" in fr_date
    assert "Monday" in en_date
    assert "October" in en_date


def test_get_short_day_names():
    fr_days = get_short_day_names("fr")
    en_days = get_short_day_names("en")

    assert fr_days[0] == "LUN"
    assert en_days[0] == "MON"


def test_resolve_user_language():
    # 1. Profile takes precedence
    profile_en = UserProfile(discord_id=123, language="en")
    assert resolve_user_language(profile=profile_en) == "en"

    profile_fr = UserProfile(discord_id=123, language="fr")
    assert resolve_user_language(profile=profile_fr) == "fr"

    # 2. Discord interaction locale fallback
    mock_interaction_en = MagicMock()
    mock_interaction_en.locale = "en-US"
    assert resolve_user_language(interaction=mock_interaction_en) == "en"

    mock_interaction_fr = MagicMock()
    mock_interaction_fr.locale = "fr"
    assert resolve_user_language(interaction=mock_interaction_fr) == "fr"

    # 3. Default fallback
    assert resolve_user_language() == "fr"


def test_localized_embed_creation():
    target_date = date(2026, 10, 12)
    course = CourseEvent(
        uid="c1",
        name="Data Governance",
        start=datetime(2026, 10, 12, 9, 0),
        end=datetime(2026, 10, 12, 13, 0),
        room="Salle 10",
        teacher="Prof Smith",
    )

    # Day embed
    embed_fr = create_day_embed(target_date, [course], lang="fr")
    embed_en = create_day_embed(target_date, [course], lang="en")
    assert "cours au programme" in (embed_fr.description or "")
    assert "classes scheduled" in (embed_en.description or "")
    assert "Salle:" in (embed_fr.fields[0].value or "")
    assert "Room:" in (embed_en.fields[0].value or "")

    # Week embed
    week_fr = create_week_embed(target_date, [course], lang="fr")
    week_en = create_week_embed(target_date, [course], lang="en")
    assert "Semaine du" in (week_fr.description or "")
    assert "Week of" in (week_en.description or "")

    # Now embed
    now_fr = create_now_embed(course, [], lang="fr")
    now_en = create_now_embed(course, [], lang="en")
    assert "En cours actuellement" in (now_fr.fields[0].name or "")
    assert "Currently in progress" in (now_en.fields[0].name or "")


def test_localized_image_rendering():
    target_date = date(2026, 10, 12)
    course = CourseEvent(
        uid="c1",
        name="Security Architecture",
        start=datetime(2026, 10, 12, 9, 0),
        end=datetime(2026, 10, 12, 13, 0),
        room="T 101",
        teacher="Clement",
    )

    buf_day_fr = render_day_image(target_date, [course], lang="fr")
    buf_day_en = render_day_image(target_date, [course], lang="en")
    assert buf_day_fr.getbuffer().nbytes > 1000
    assert buf_day_en.getbuffer().nbytes > 1000

    buf_week_fr = render_week_image(target_date, [course], lang="fr")
    buf_week_en = render_week_image(target_date, [course], lang="en")
    assert buf_week_fr.getbuffer().nbytes > 1000
    assert buf_week_en.getbuffer().nbytes > 1000
