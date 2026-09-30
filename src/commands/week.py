"""Slash command: /week to view an entire week's schedule."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands

from database import get_user_profile
from services.embed_builder import create_week_embed
from services.ical_service import get_week_schedule
from services.image_renderer import render_week_image
from ui.views import WeekScheduleView

logger = logging.getLogger(__name__)


@app_commands.command(
    name="week",
    description="Afficher l'emploi du temps EPSI pour une semaine complète",
)
@app_commands.describe(
    date="Date comprise dans la semaine au format JJ/MM/AAAA (par défaut: semaine actuelle)",
    image="Afficher sous forme de calendrier image ou d'embed texte",
    url="URL iCal directe optionnelle (si non enregistré)",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def week_command(
    interaction: discord.Interaction,
    date: str | None = None,
    image: bool | None = None,
    url: str | None = None,
) -> None:
    """Execute /week slash command."""
    await interaction.response.defer(ephemeral=False)

    target_url = url
    prefer_image = True if image is None else image

    if not target_url:
        profile = await get_user_profile(interaction.user.id)
        if profile and profile.ical_url:
            target_url = profile.ical_url
            if image is None:
                prefer_image = profile.prefer_image
        else:
            await interaction.followup.send(
                "❌ **Vous n'avez pas encore enregistré votre lien iCal !**\n"
                "Utilisez la commande `/settings register <votre_lien_ical>` pour lier votre emploi du temps "
                "ou passez le paramètre `url:` dans la commande.",
                ephemeral=True,
            )
            return

    target_date = datetime.now().date()
    if date:
        try:
            target_date = datetime.strptime(date, "%d/%m/%Y").date()
        except ValueError:
            await interaction.followup.send(
                "❌ **Format de date invalide.** Veuillez utiliser le format `JJ/MM/AAAA` (ex: `15/10/2026`).",
                ephemeral=True,
            )
            return

    start_of_week = target_date - timedelta(days=target_date.weekday())

    try:
        courses = await get_week_schedule(target_url, start_of_week)
        view = WeekScheduleView(
            ical_url=target_url,
            start_of_week=start_of_week,
            show_image=prefer_image,
            user_id=interaction.user.id,
        )

        if prefer_image:
            img_buf = render_week_image(start_of_week, courses)
            file = discord.File(img_buf, filename=f"week_{start_of_week.isoformat()}.png")
            await interaction.followup.send(file=file, view=view)
        else:
            embed = create_week_embed(start_of_week, courses)
            await interaction.followup.send(embed=embed, view=view)

    except Exception as e:
        logger.error(f"Error executing /week: {e}", exc_info=True)
        await interaction.followup.send(
            "⚠️ Une erreur est survenue lors de la récupération ou de l'affichage de votre emploi du temps. "
            "Vérifiez que votre lien Hyperplanning est toujours valide.",
            ephemeral=True,
        )
