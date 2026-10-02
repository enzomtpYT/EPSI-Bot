"""Unit tests for French public holidays service."""

from datetime import date

import pytest

from services.holidays import (
    calculate_french_public_holidays,
    get_easter_date,
    get_french_public_holidays,
    get_public_holiday,
)


def test_easter_dates():
    """Verify Meeus algorithm calculates correct Easter dates for known years."""
    # 2024: March 31
    assert get_easter_date(2024) == date(2024, 3, 31)
    # 2025: April 20
    assert get_easter_date(2025) == date(2025, 4, 20)
    # 2026: April 5
    assert get_easter_date(2026) == date(2026, 4, 5)
    # 2027: March 28
    assert get_easter_date(2027) == date(2027, 3, 28)


def test_french_public_holidays_offline_2026():
    """Verify offline calculation generates all 11 statutory French holidays for 2026."""
    holidays = calculate_french_public_holidays(2026)
    assert len(holidays) == 11

    # Fixed holidays
    assert date(2026, 1, 1) in holidays
    assert holidays[date(2026, 1, 1)]["fr"] == "Jour de l'An"
    assert holidays[date(2026, 1, 1)]["en"] == "New Year's Day"

    assert date(2026, 5, 1) in holidays
    assert holidays[date(2026, 5, 1)]["fr"] == "Fête du Travail"

    assert date(2026, 5, 8) in holidays
    assert holidays[date(2026, 5, 8)]["fr"] == "Victoire 1945"

    assert date(2026, 7, 14) in holidays
    assert holidays[date(2026, 7, 14)]["fr"] == "Fête Nationale"

    assert date(2026, 8, 15) in holidays
    assert holidays[date(2026, 8, 15)]["fr"] == "Assomption"

    assert date(2026, 11, 1) in holidays
    assert holidays[date(2026, 11, 1)]["fr"] == "Toussaint"

    assert date(2026, 11, 11) in holidays
    assert holidays[date(2026, 11, 11)]["fr"] == "Armistice 1918"

    assert date(2026, 12, 25) in holidays
    assert holidays[date(2026, 12, 25)]["fr"] == "Noël"

    # Movable holidays for 2026 (Easter Sunday is April 5)
    # Lundi de Pâques: April 6
    assert date(2026, 4, 6) in holidays
    assert holidays[date(2026, 4, 6)]["fr"] == "Lundi de Pâques"
    assert holidays[date(2026, 4, 6)]["en"] == "Easter Monday"

    # Ascension: May 14 (April 5 + 39 days)
    assert date(2026, 5, 14) in holidays
    assert holidays[date(2026, 5, 14)]["fr"] == "Ascension"

    # Lundi de Pentecôte: May 25 (April 5 + 50 days)
    assert date(2026, 5, 25) in holidays
    assert holidays[date(2026, 5, 25)]["fr"] == "Lundi de Pentecôte"


@pytest.mark.asyncio
async def test_get_french_public_holidays_bilingual():
    """Verify get_french_public_holidays returns localized names."""
    fr_holidays = await get_french_public_holidays(2026, lang="fr")
    en_holidays = await get_french_public_holidays(2026, lang="en")

    assert date(2026, 5, 1) in fr_holidays
    assert fr_holidays[date(2026, 5, 1)] == "Fête du Travail"

    assert date(2026, 5, 1) in en_holidays
    assert en_holidays[date(2026, 5, 1)] == "Labour Day"


@pytest.mark.asyncio
async def test_get_public_holiday_lookup():
    """Verify lookup helper returns holiday name for holiday dates and None otherwise."""
    # May 1st 2026 is a holiday
    assert await get_public_holiday(date(2026, 5, 1), lang="fr") == "Fête du Travail"
    assert await get_public_holiday(date(2026, 5, 1), lang="en") == "Labour Day"

    # May 2nd 2026 is not a holiday
    assert await get_public_holiday(date(2026, 5, 2)) is None
