"""Authentication routes for Discord OAuth2."""

from __future__ import annotations

import logging
import secrets
from urllib.parse import quote_plus

import aiohttp
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from config import settings
from database import get_or_create_user_profile, get_user_profile

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="", tags=["auth"])

DISCORD_API_BASE = "https://discord.com/api"


@auth_router.get("/auth/login")
async def login(request: Request) -> RedirectResponse:
    """Redirect user to Discord OAuth2 authorization URL with CSRF state token."""
    if not settings.discord_client_id or not settings.discord_client_secret:
        logger.warning("Discord OAuth2 credentials not set in environment.")
        return RedirectResponse(url="/?error=oauth_not_configured")

    # Generate cryptographically secure CSRF state token
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    redirect_uri = quote_plus(settings.discord_redirect_uri)
    auth_url = (
        f"{DISCORD_API_BASE}/oauth2/authorize"
        f"?client_id={settings.discord_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=identify"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)


@auth_router.get("/auth/callback")
async def callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
) -> RedirectResponse:
    """Handle OAuth2 callback from Discord with CSRF state verification."""
    # 1. CSRF State validation
    stored_state = request.session.pop("oauth_state", None)
    if not stored_state or not state or stored_state != state:
        logger.warning("OAuth2 callback rejected: CSRF state parameter missing or mismatched.")
        return RedirectResponse(url="/?error=csrf_state_invalid")

    if error or not code:
        logger.warning(f"OAuth2 callback error or missing code: {error}")
        return RedirectResponse(url="/?error=auth_failed")

    token_url = f"{DISCORD_API_BASE}/oauth2/token"
    token_data = {
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.discord_redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(token_url, data=token_data, headers=headers) as token_resp:
            if token_resp.status != 200:
                resp_text = await token_resp.text()
                logger.error(f"Failed to exchange token with Discord: {resp_text}")
                return RedirectResponse(url="/?error=token_exchange_failed")
            token_json = await token_resp.json()

        access_token = token_json.get("access_token")
        if not access_token:
            return RedirectResponse(url="/?error=missing_token")

        user_headers = {"Authorization": f"Bearer {access_token}"}
        async with session.get(f"{DISCORD_API_BASE}/users/@me", headers=user_headers) as user_resp:
            if user_resp.status != 200:
                logger.error(f"Failed to fetch Discord user info: {user_resp.status}")
                return RedirectResponse(url="/?error=user_fetch_failed")
            user_json = await user_resp.json()

    discord_id = int(user_json["id"])
    username = user_json.get("username", "Utilisateur")
    avatar = user_json.get("avatar")
    global_name = user_json.get("global_name") or username

    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png"
        if avatar
        else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    # Ensure profile exists in DB
    await get_or_create_user_profile(
        discord_id,
        display_name=global_name,
        avatar_url=avatar_url,
    )

    # Save to session
    request.session["user"] = {
        "discord_id": discord_id,
        "username": username,
        "global_name": global_name,
        "avatar_url": avatar_url,
    }

    logger.info(f"User {username} ({discord_id}) logged in successfully via Discord OAuth2.")
    return RedirectResponse(url="/")


@auth_router.get("/auth/logout")
async def logout(request: Request) -> RedirectResponse:
    """Log out current user and clear session."""
    request.session.clear()
    return RedirectResponse(url="/")


@auth_router.get("/api/me")
async def get_current_user_info(request: Request) -> dict:
    """Return current logged-in user profile and settings."""
    user = request.session.get("user")
    oauth_configured = bool(settings.discord_client_id and settings.discord_client_secret)

    if not user:
        return {"logged_in": False, "oauth_configured": oauth_configured}

    discord_id = user["discord_id"]
    profile = await get_user_profile(discord_id)

    return {
        "logged_in": True,
        "oauth_configured": oauth_configured,
        "user": user,
        "settings": {
            "ical_url": profile.ical_url if profile else None,
            "daily_notifications": profile.daily_notifications if profile else False,
            "weekly_notifications": profile.weekly_notifications if profile else False,
            "prefer_image": profile.prefer_image if profile else True,
            "language": profile.language if profile else "fr",
            "show_work_days": profile.show_work_days if profile else True,
            "timezone": profile.timezone if profile else "Europe/Paris",
            "share_enabled": profile.share_enabled if profile else False,
            "share_token": profile.share_token if profile else None,
        },
    }
