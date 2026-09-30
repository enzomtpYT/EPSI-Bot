"""API routes for schedule retrieval and user settings management."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from dateutil import parser
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from database import get_user_profile, update_user_full_settings
from services.ical_service import get_week_schedule

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])


class UpdateSettingsRequest(BaseModel):
    """Payload for updating user notification, language, and calendar settings."""

    ical_url: str | None = None
    daily_notifications: bool | None = None
    weekly_notifications: bool | None = None
    prefer_image: bool | None = None
    language: str | None = None


@api_router.post("/settings")
async def update_settings(payload: UpdateSettingsRequest, request: Request) -> dict[str, Any]:
    """Update settings for the currently authenticated user."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=401, detail="Connexion requise pour modifier les paramètres."
        )

    discord_id = user["discord_id"]
    updated_profile = await update_user_full_settings(
        discord_id,
        ical_url=payload.ical_url,
        daily_notifications=payload.daily_notifications,
        weekly_notifications=payload.weekly_notifications,
        prefer_image=payload.prefer_image,
        language=payload.language,
    )

    return {
        "success": True,
        "settings": {
            "ical_url": updated_profile.ical_url,
            "daily_notifications": updated_profile.daily_notifications,
            "weekly_notifications": updated_profile.weekly_notifications,
            "prefer_image": updated_profile.prefer_image,
            "language": updated_profile.language,
        },
    }


def parse_date_safely(date_str: str) -> date:
    """Parse date in ISO (YYYY-MM-DD) or European (DD-MM-YYYY) format."""
    clean = date_str.strip()
    if "-" in clean:
        parts = clean.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return date.fromisoformat(clean)
    return parser.parse(clean, dayfirst=True).date()


@api_router.get("/schedule/week")
async def get_schedule_week(
    request: Request,
    date_str: str = Query(
        ..., alias="date", description="Reference date (YYYY-MM-DD or DD-MM-YYYY)"
    ),
    url: str | None = Query(None, description="Direct iCal URL (optional if user logged in)"),
    cache_bust: str | None = Query(None, alias="_", description="Cache buster timestamp"),
) -> list[list[dict[str, Any]]]:
    """Fetch and parse week schedule for the given date and iCal source.

    Returns a 5-element list corresponding to Monday..Friday.
    """
    # 1. Determine iCal URL
    target_url = url.strip() if url and url.strip() else None

    if not target_url:
        user = request.session.get("user")
        if user:
            profile = await get_user_profile(user["discord_id"])
            if profile and profile.ical_url:
                target_url = profile.ical_url

    if not target_url:
        raise HTTPException(
            status_code=400,
            detail="Aucun lien iCal fourni. Veuillez entrer un lien ou vous connecter.",
        )

    # Convert webcal:// to https://
    if target_url.startswith("webcal://"):
        target_url = "https://" + target_url[len("webcal://") :]

    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        raise HTTPException(
            status_code=400, detail="Format d'URL iCal invalide (doit commencer par https://)."
        )

    # 2. Parse reference date
    try:
        parsed_date: date = parse_date_safely(date_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Date invalide: {e}")

    # Monday of the week
    monday = parsed_date - timedelta(days=parsed_date.weekday())

    # 3. Fetch courses
    try:
        courses = await get_week_schedule(target_url, parsed_date, force_refresh=bool(cache_bust))
    except Exception as e:
        logger.error(f"Error fetching week schedule: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la récupération de l'iCal: {e}"
        )

    # 4. Group courses by day of week (Monday=0 to Friday=4)
    week_days: list[list[dict[str, Any]]] = [[] for _ in range(5)]

    for course in courses:
        day_offset = (course.event_date - monday).days
        if 0 <= day_offset < 5:
            week_days[day_offset].append(
                {
                    "name": course.name,
                    "room": course.room or "Inconnue",
                    "teacher": course.teacher or "Inconnu",
                    "date": course.event_date.isoformat(),
                    "start_time": course.start.strftime("%H:%M"),
                    "end_time": course.end.strftime("%H:%M"),
                    "teams_link": course.teams_link,
                }
            )

    return week_days
