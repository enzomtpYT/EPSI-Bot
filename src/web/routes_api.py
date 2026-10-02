"""API routes for schedule retrieval and user settings management."""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any

from dateutil import parser
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from database import (
    add_whitelisted_viewer,
    generate_or_get_share_token,
    get_schedules_shared_with,
    get_user_by_share_token,
    get_user_profile,
    get_whitelisted_viewers,
    is_user_authorized_to_view,
    remove_whitelisted_viewer,
    update_user_full_settings,
)
from services.ical_service import convert_course_timezone, get_week_schedule
from services.schedule_enricher import enrich_schedule
from services.security import validate_safe_url

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])


class UpdateSettingsRequest(BaseModel):
    """Payload for updating user notification, language, and calendar settings."""

    ical_url: str | None = Field(None, max_length=2048)
    daily_notifications: bool | None = None
    weekly_notifications: bool | None = None
    prefer_image: bool | None = None
    language: str | None = Field(None, max_length=10)
    show_work_days: bool | None = None
    timezone: str | None = Field(None, max_length=100)
    share_enabled: bool | None = None


class AddWhitelistRequest(BaseModel):
    """Payload for adding a Discord user ID to whitelist."""

    viewer_id: int | str


@api_router.post("/settings")
async def update_settings(payload: UpdateSettingsRequest, request: Request) -> dict[str, Any]:
    """Update settings for the currently authenticated user."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=401, detail="Connexion requise pour modifier les paramètres."
        )

    discord_id = user["discord_id"]
    safe_ical_url = payload.ical_url
    if safe_ical_url and safe_ical_url.strip():
        try:
            safe_ical_url = validate_safe_url(safe_ical_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Lien iCal invalide : {e}")

    updated_profile = await update_user_full_settings(
        discord_id,
        ical_url=safe_ical_url,
        daily_notifications=payload.daily_notifications,
        weekly_notifications=payload.weekly_notifications,
        prefer_image=payload.prefer_image,
        language=payload.language,
        show_work_days=payload.show_work_days,
        timezone=payload.timezone,
        share_enabled=payload.share_enabled,
    )

    return {
        "success": True,
        "settings": {
            "ical_url": updated_profile.ical_url,
            "daily_notifications": updated_profile.daily_notifications,
            "weekly_notifications": updated_profile.weekly_notifications,
            "prefer_image": updated_profile.prefer_image,
            "language": updated_profile.language,
            "show_work_days": updated_profile.show_work_days,
            "timezone": updated_profile.timezone,
            "share_enabled": updated_profile.share_enabled,
            "share_token": updated_profile.share_token,
        },
    }


@api_router.get("/share/whitelist")
async def get_whitelist(request: Request) -> dict[str, Any]:
    """Get list of whitelisted viewer IDs for the current user."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    viewers = await get_whitelisted_viewers(user["discord_id"])
    profile = await get_user_profile(user["discord_id"])
    viewer_details: list[dict[str, Any]] = []
    for vid in viewers:
        v_prof = await get_user_profile(vid)
        viewer_details.append(
            {
                "id": str(vid),
                "display_name": v_prof.display_name
                if (v_prof and v_prof.display_name)
                else f"User {vid}",
                "avatar_url": v_prof.avatar_url if v_prof else None,
            }
        )
    return {
        "share_enabled": profile.share_enabled if profile else False,
        "share_token": profile.share_token if profile else None,
        "viewers": [str(v) for v in viewers],
        "viewer_details": viewer_details,
    }


@api_router.post("/share/whitelist")
async def add_whitelist(payload: AddWhitelistRequest, request: Request) -> dict[str, Any]:
    """Add a viewer ID to the current user's whitelist."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    try:
        vid = int(str(payload.viewer_id).strip())
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="ID Discord invalide.")
    success = await add_whitelisted_viewer(owner_id=user["discord_id"], viewer_id=vid)
    return {"success": success}


@api_router.delete("/share/whitelist/{viewer_id}")
async def remove_whitelist(viewer_id: str, request: Request) -> dict[str, Any]:
    """Remove a viewer ID from the current user's whitelist."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    try:
        vid = int(viewer_id.strip())
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="ID Discord invalide.")
    success = await remove_whitelisted_viewer(owner_id=user["discord_id"], viewer_id=vid)
    return {"success": success}


@api_router.post("/share/token/regenerate")
async def regenerate_share_token(request: Request) -> dict[str, Any]:
    """Regenerate secret web share token."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    new_token = await generate_or_get_share_token(user["discord_id"], force_new=True)
    return {"token": new_token}


@api_router.get("/shared-with-me")
async def get_shared_with_me(request: Request) -> list[dict[str, Any]]:
    """Get schedules shared with the current user."""
    user = request.session.get("user")
    if not user:
        return []
    owners = await get_schedules_shared_with(user["discord_id"])
    return [
        {
            "discord_id": str(o.discord_id),
            "display_name": o.display_name or f"User {o.discord_id}",
            "avatar_url": o.avatar_url,
        }
        for o in owners
    ]


@api_router.get("/timezones")
async def get_timezones() -> list[str]:
    """Return all available IANA timezones sorted alphabetically."""
    import zoneinfo

    return sorted(
        [tz for tz in zoneinfo.available_timezones() if "/" in tz or tz in {"UTC", "GMT"}]
    )


DATE_PATTERN = re.compile(r"^\d{2,4}[-/.]\d{1,2}[-/.]\d{2,4}$")


def parse_date_safely(date_str: str) -> date:
    """Parse date in ISO (YYYY-MM-DD) or European (DD-MM-YYYY) format with pre-validation."""
    clean = date_str.strip()
    if not DATE_PATTERN.match(clean):
        raise ValueError("Format de date invalide.")
    if "-" in clean:
        parts = clean.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return date.fromisoformat(clean)
    return parser.parse(clean, dayfirst=True).date()


@api_router.get("/schedule/week")
async def get_schedule_week(
    request: Request,
    date_str: str = Query(
        ...,
        alias="date",
        max_length=30,
        description="Reference date (YYYY-MM-DD or DD-MM-YYYY)",
    ),
    url: str | None = Query(
        None, max_length=2048, description="Direct iCal URL (optional if user logged in)"
    ),
    owner_id: int | None = Query(
        None, description="Discord ID of schedule owner if viewing shared"
    ),
    share_token: str | None = Query(
        None,
        alias="token",
        max_length=64,
        description="Secret share token if accessing via share link",
    ),
    tz: str = Query("Europe/Paris", max_length=100, description="Viewer local timezone"),
    work_days: bool | None = Query(
        None, description="Display synthetic work/alternance on empty weekdays"
    ),
    lang: str = Query("fr", max_length=10, description="Language preference ('fr' or 'en')"),
    cache_bust: str | None = Query(
        None, alias="_", max_length=50, description="Cache buster timestamp"
    ),
) -> list[list[dict[str, Any]]]:
    """Fetch and parse week schedule for the given date and iCal source.

    Returns a 5-element list corresponding to Monday..Friday.
    """
    # 1. Determine iCal URL and authorization
    target_url = url.strip() if url and url.strip() else None
    profile = None
    show_work = True
    is_shared_view = False

    user = request.session.get("user")
    if user:
        profile = await get_user_profile(user["discord_id"])

    if share_token:
        owner = await get_user_by_share_token(share_token)
        if not owner or not owner.share_enabled or not owner.ical_url:
            raise HTTPException(status_code=403, detail="Lien de partage invalide ou expiré.")
        target_url = owner.ical_url
        show_work = owner.show_work_days
        is_shared_view = True
    elif owner_id:
        if not user:
            raise HTTPException(
                status_code=401, detail="Connexion requise pour consulter un planning partagé."
            )
        authorized = await is_user_authorized_to_view(
            owner_id=owner_id, viewer_id=user["discord_id"]
        )
        if not authorized:
            raise HTTPException(
                status_code=403, detail="Vous n'êtes pas autorisé à consulter cet emploi du temps."
            )
        owner = await get_user_profile(owner_id)
        if not owner or not owner.ical_url:
            raise HTTPException(
                status_code=404, detail="Cet utilisateur n'a pas configuré son emploi du temps."
            )
        target_url = owner.ical_url
        show_work = owner.show_work_days
        if user["discord_id"] != owner_id:
            is_shared_view = True
    else:
        if not target_url and profile and profile.ical_url:
            target_url = profile.ical_url
        if work_days is not None:
            show_work = work_days
        elif profile is not None:
            show_work = profile.show_work_days

    if not target_url:
        raise HTTPException(
            status_code=400,
            detail="Aucun lien iCal fourni. Veuillez entrer un lien ou vous connecter.",
        )

    # Validate against SSRF and unsafe schemes
    try:
        target_url = validate_safe_url(target_url)
    except ValueError as e:
        logger.warning(f"Rejected unsafe iCal URL: {e}")
        raise HTTPException(
            status_code=400,
            detail="Lien iCal invalide ou interdit par la politique de sécurité.",
        )

    # 2. Parse reference date
    try:
        parsed_date: date = parse_date_safely(date_str)
    except Exception as e:
        logger.warning(f"Invalid date string '{date_str}': {e}")
        raise HTTPException(
            status_code=400,
            detail="Format de date invalide (attendu : AAAA-MM-JJ ou JJ-MM-AAAA).",
        )

    # Monday of the week
    monday = parsed_date - timedelta(days=parsed_date.weekday())

    # 3. Fetch courses
    try:
        raw_courses = await get_week_schedule(
            target_url, parsed_date, force_refresh=bool(cache_bust)
        )
        end_of_week = monday + timedelta(days=6)
        courses = await enrich_schedule(
            raw_courses,
            monday,
            end_of_week,
            show_work_days=show_work,
            lang=lang,
        )
    except Exception as e:
        logger.error(f"Error fetching week schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Impossible de récupérer ou d'analyser l'emploi du temps.",
        )

    # 4. Group courses by day of week (Monday=0 to Friday=4)
    week_days: list[list[dict[str, Any]]] = [[] for _ in range(5)]

    for course in courses:
        conv_course = convert_course_timezone(course, tz)
        day_offset = (course.event_date - monday).days
        if 0 <= day_offset < 5:
            week_days[day_offset].append(
                {
                    "name": course.name,
                    "room": course.room or ("Inconnue" if lang != "en" else "Unknown"),
                    "teacher": course.teacher or ("Inconnu" if lang != "en" else "Unknown"),
                    "date": course.event_date.isoformat(),
                    "start_time": conv_course.start.strftime("%H:%M"),
                    "end_time": conv_course.end.strftime("%H:%M"),
                    "school_start_time": course.start.strftime("%H:%M"),
                    "school_end_time": course.end.strftime("%H:%M"),
                    "timezone": tz,
                    "school_timezone": "Europe/Paris",
                    "teams_link": None if is_shared_view else course.teams_link,
                    "event_type": course.event_type,
                }
            )

    return week_days
