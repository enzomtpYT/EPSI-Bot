"""French national public holidays (jours fériés) service.

Fetches official data from https://calendrier.api.gouv.fr/jours-feries/
with offline calculation fallback using the Meeus/Jones/Butcher Easter algorithm.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import aiohttp

logger = logging.getLogger(__name__)

# Cache: year -> dict[date, dict[str, str]] (keys: 'fr', 'en')
_HOLIDAYS_CACHE: dict[int, dict[date, dict[str, str]]] = {}

# Canonical translations of French statutory public holidays (Article L. 3133-1)
HOLIDAY_NAMES: dict[str, dict[str, str]] = {
    "1er janvier": {"fr": "Jour de l'An", "en": "New Year's Day"},
    "Lundi de Pâques": {"fr": "Lundi de Pâques", "en": "Easter Monday"},
    "1er mai": {"fr": "Fête du Travail", "en": "Labour Day"},
    "8 mai": {"fr": "Victoire 1945", "en": "Victory in Europe Day"},
    "Ascension": {"fr": "Ascension", "en": "Ascension Day"},
    "Lundi de Pentecôte": {"fr": "Lundi de Pentecôte", "en": "Whit Monday"},
    "14 juillet": {"fr": "Fête Nationale", "en": "Bastille Day"},
    "Assomption": {"fr": "Assomption", "en": "Assumption of Mary"},
    "Toussaint": {"fr": "Toussaint", "en": "All Saints' Day"},
    "11 novembre": {"fr": "Armistice 1918", "en": "Armistice Day"},
    "Jour de Noël": {"fr": "Noël", "en": "Christmas Day"},
    "Noël": {"fr": "Noël", "en": "Christmas Day"},
}


def get_easter_date(year: int) -> date:
    """Calculate the date of Gregorian Easter Sunday using the Meeus algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def calculate_french_public_holidays(year: int) -> dict[date, dict[str, str]]:
    """Compute statutory French public holidays offline with bilingual support."""
    easter = get_easter_date(year)
    easter_monday = easter + timedelta(days=1)
    ascension = easter + timedelta(days=39)
    whit_monday = easter + timedelta(days=50)

    holidays: dict[date, dict[str, str]] = {
        date(year, 1, 1): {"fr": "Jour de l'An", "en": "New Year's Day"},
        easter_monday: {"fr": "Lundi de Pâques", "en": "Easter Monday"},
        date(year, 5, 1): {"fr": "Fête du Travail", "en": "Labour Day"},
        date(year, 5, 8): {"fr": "Victoire 1945", "en": "Victory in Europe Day"},
        ascension: {"fr": "Ascension", "en": "Ascension Day"},
        whit_monday: {"fr": "Lundi de Pentecôte", "en": "Whit Monday"},
        date(year, 7, 14): {"fr": "Fête Nationale", "en": "Bastille Day"},
        date(year, 8, 15): {"fr": "Assomption", "en": "Assumption of Mary"},
        date(year, 11, 1): {"fr": "Toussaint", "en": "All Saints' Day"},
        date(year, 11, 11): {"fr": "Armistice 1918", "en": "Armistice Day"},
        date(year, 12, 25): {"fr": "Noël", "en": "Christmas Day"},
    }
    return holidays


async def fetch_api_gouv_holidays(year: int) -> dict[date, dict[str, str]]:
    """Fetch French public holidays from official api.gouv.fr service."""
    url = f"https://calendrier.api.gouv.fr/jours-feries/metropole/{year}.json"
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"api.gouv.fr returned status {response.status}")
            data = await response.json()

    result: dict[date, dict[str, str]] = {}
    for d_str, raw_name in data.items():
        dt = date.fromisoformat(d_str)
        # Match standard holiday translation if known
        mapping = HOLIDAY_NAMES.get(raw_name)
        if mapping:
            result[dt] = mapping
        else:
            result[dt] = {"fr": raw_name, "en": raw_name}

    return result


async def get_french_public_holidays(year: int, lang: str = "fr") -> dict[date, str]:
    """Return dictionary mapping date -> localized holiday name for given year.

    Uses api.gouv.fr if available, falling back to pure Python offline calculation.
    """
    if year not in _HOLIDAYS_CACHE:
        try:
            fetched = await fetch_api_gouv_holidays(year)
            _HOLIDAYS_CACHE[year] = fetched
        except Exception as e:
            logger.warning(
                f"Could not fetch holidays from api.gouv.fr for {year} ({e}). Using offline calculation."
            )
            _HOLIDAYS_CACHE[year] = calculate_french_public_holidays(year)

    year_data = _HOLIDAYS_CACHE[year]
    lang_key = "en" if lang == "en" else "fr"
    return {d: names.get(lang_key, names.get("fr", "")) for d, names in year_data.items()}


async def get_public_holiday(target_date: date, lang: str = "fr") -> str | None:
    """Return holiday name if target_date is a French public holiday, or None."""
    holidays = await get_french_public_holidays(target_date.year, lang=lang)
    return holidays.get(target_date)
