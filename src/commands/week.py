"""Slash command: /week to view an entire week's schedule."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands

from database import get_user_profile, is_user_authorized_to_view
from services.embed_builder import create_week_embed
from services.i18n import resolve_user_language
from services.ical_service import get_week_schedule, strip_teams_links
from services.image_renderer import render_week_image
from services.schedule_enricher import enrich_schedule
from ui.views import WeekScheduleView

logger = logging.getLogger(__name__)


async def handle_week_command(
    interaction: discord.Interaction,
    date: str | None = None,
    image: bool | None = None,
    url: str | None = None,
    user: discord.User | None = None,
) -> None:
    """Handle core logic for week schedule display."""
    await interaction.response.defer(ephemeral=False)

    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)
    viewer_tz = profile.timezone if (profile and profile.timezone) else "Europe/Paris"

    target_url = url
    prefer_image = True if image is None else image
    show_work = profile.show_work_days if profile else True
    is_shared_view = False

    # If viewing another user's schedule
    if user is not None and user.id != interaction.user.id:
        is_shared_view = True
        authorized = await is_user_authorized_to_view(
            owner_id=user.id, viewer_id=interaction.user.id
        )
        if not authorized:
            denied_msg = (
                f"❌ **Access Denied**: {user.mention} has not authorized you to view their schedule."
                if lang == "en"
                else f"❌ **Accès refusé** : {user.mention} ne vous a pas autorisé à consulter son emploi du temps."
            )
            await interaction.followup.send(denied_msg, ephemeral=True)
            return

        owner_profile = await get_user_profile(user.id)
        if not owner_profile or not owner_profile.ical_url:
            no_sched_msg = (
                f"❌ {user.mention} has not registered an iCal link yet."
                if lang == "en"
                else f"❌ {user.mention} n'a pas encore configuré son emploi du temps."
            )
            await interaction.followup.send(no_sched_msg, ephemeral=True)
            return

        target_url = owner_profile.ical_url
        show_work = owner_profile.show_work_days

    if not target_url:
        if profile and profile.ical_url:
            target_url = profile.ical_url
            if image is None:
                prefer_image = profile.prefer_image
        else:
            missing_msg = (
                "❌ **You haven't registered your iCal link yet!**\n"
                "Use `/settings register <your_ical_url>` to configure your schedule or pass the `url:` parameter."
                if lang == "en"
                else "❌ **Vous n'avez pas encore enregistré votre lien iCal !**\n"
                "Utilisez la commande `/settings register <votre_lien_ical>` pour lier votre emploi du temps "
                "ou passez le paramètre `url:` dans la commande."
            )
            await interaction.followup.send(missing_msg, ephemeral=True)
            return

    target_date = datetime.now().date()
    if date:
        try:
            target_date = datetime.strptime(date, "%d/%m/%Y").date()
        except ValueError:
            invalid_date_msg = (
                "❌ **Invalid date format.** Please use `DD/MM/YYYY` (e.g. `15/10/2026`)."
                if lang == "en"
                else "❌ **Format de date invalide.** Veuillez utiliser le format `JJ/MM/AAAA` (ex: `15/10/2026`)."
            )
            await interaction.followup.send(invalid_date_msg, ephemeral=True)
            return

    start_of_week = target_date - timedelta(days=target_date.weekday())

    try:
        raw_courses = await get_week_schedule(target_url, start_of_week)
        end_of_week = start_of_week + timedelta(days=6)
        courses = await enrich_schedule(
            raw_courses,
            start_of_week,
            end_of_week,
            show_work_days=show_work,
            lang=lang,
        )
        if is_shared_view:
            courses = strip_teams_links(courses)

        view = WeekScheduleView(
            ical_url=target_url,
            start_of_week=start_of_week,
            show_image=prefer_image,
            user_id=interaction.user.id,
            lang=lang,
            show_work_days=show_work,
            target_tz=viewer_tz,
            hide_teams=is_shared_view,
            courses=courses,
        )

        if prefer_image:
            img_buf = render_week_image(start_of_week, courses, lang=lang, target_tz=viewer_tz)
            file = discord.File(img_buf, filename=f"week_{start_of_week.isoformat()}.png")
            await interaction.followup.send(file=file, view=view)
        else:
            embed = create_week_embed(start_of_week, courses, lang=lang)
            await interaction.followup.send(embed=embed, view=view)

    except Exception as e:
        logger.error(f"Error executing /week: {e}", exc_info=True)
        err_msg = (
            "⚠️ An error occurred while fetching or displaying your schedule. Please ensure your Hyperplanning link is valid."
            if lang == "en"
            else "⚠️ Une erreur est survenue lors de la récupération ou de l'affichage de votre emploi du temps. "
            "Vérifiez que votre lien Hyperplanning est toujours valide."
        )
        await interaction.followup.send(err_msg, ephemeral=True)


@app_commands.command(
    name="week",
    description="Afficher l'emploi du temps EPSI pour une semaine complète / View weekly schedule",
)
@app_commands.describe(
    date="Date comprise dans la semaine au format JJ/MM/AAAA / Date DD/MM/YYYY",
    image="Afficher sous forme de calendrier image ou d'embed / Image or Text embed",
    url="URL iCal directe optionnelle / Direct iCal URL",
    user="Utilisateur dont vous souhaitez voir l'emploi du temps / User whose schedule to view",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def week_command(
    interaction: discord.Interaction,
    date: str | None = None,
    image: bool | None = None,
    url: str | None = None,
    user: discord.User | None = None,
) -> None:
    """Execute /week slash command."""
    await handle_week_command(interaction, date=date, image=image, url=url, user=user)
