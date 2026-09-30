"""Background cron jobs for daily and weekly DM schedule reminders."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import discord

from database import (
    get_users_for_daily_notifications,
    get_users_for_weekly_notifications,
)
from services.embed_builder import create_day_embed, create_week_embed
from services.i18n import t
from services.ical_service import get_day_schedule, get_week_schedule
from services.image_renderer import render_day_image, render_week_image

logger = logging.getLogger(__name__)


async def run_daily_notification_job(bot: discord.Client) -> None:
    """Send daily schedule via DM every day at 06:00 to subscribed users."""
    logger.info("Executing daily schedule notifications job...")
    users = await get_users_for_daily_notifications()
    today = date.today()

    for user_profile in users:
        if not user_profile.ical_url:
            continue

        lang = user_profile.language or "fr"

        try:
            discord_user = bot.get_user(user_profile.discord_id)
            if discord_user is None:
                discord_user = await bot.fetch_user(user_profile.discord_id)

            courses = await get_day_schedule(user_profile.ical_url, today)
            content = t("cron_daily_title", lang=lang)

            if user_profile.prefer_image:
                img_buf = render_day_image(today, courses, lang=lang)
                file = discord.File(img_buf, filename=f"emploi_du_temps_{today.isoformat()}.png")
                await discord_user.send(content=content, file=file)
            else:
                embed = create_day_embed(today, courses, lang=lang)
                await discord_user.send(content=content, embed=embed)

            logger.info(f"Daily notification sent to user {user_profile.discord_id}")
        except discord.Forbidden:
            logger.warning(f"Forbidden: Cannot send DM to user {user_profile.discord_id}")
        except Exception as e:
            logger.error(f"Error sending daily notification to {user_profile.discord_id}: {e}")


async def run_weekly_notification_job(bot: discord.Client) -> None:
    """Send weekly schedule via DM every Monday at 06:00 to subscribed users."""
    logger.info("Executing weekly schedule notifications job...")
    users = await get_users_for_weekly_notifications()
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    for user_profile in users:
        if not user_profile.ical_url:
            continue

        lang = user_profile.language or "fr"

        try:
            discord_user = bot.get_user(user_profile.discord_id)
            if discord_user is None:
                discord_user = await bot.fetch_user(user_profile.discord_id)

            courses = await get_week_schedule(user_profile.ical_url, start_of_week)
            content = t("cron_weekly_title", lang=lang)

            if user_profile.prefer_image:
                img_buf = render_week_image(start_of_week, courses, lang=lang)
                file = discord.File(img_buf, filename=f"semaine_{start_of_week.isoformat()}.png")
                await discord_user.send(content=content, file=file)
            else:
                embed = create_week_embed(start_of_week, courses, lang=lang)
                await discord_user.send(content=content, embed=embed)

            logger.info(f"Weekly notification sent to user {user_profile.discord_id}")
        except discord.Forbidden:
            logger.warning(f"Forbidden: Cannot send DM to user {user_profile.discord_id}")
        except Exception as e:
            logger.error(f"Error sending weekly notification to {user_profile.discord_id}: {e}")
