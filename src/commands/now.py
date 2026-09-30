"""Slash command: /now to check current class and upcoming classes."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

from database import get_user_profile
from services.embed_builder import create_now_embed
from services.i18n import resolve_user_language
from services.ical_service import get_next_classes

logger = logging.getLogger(__name__)


@app_commands.command(
    name="now",
    description="Afficher le cours en cours et les prochains cours à venir / Live & upcoming classes",
)
@app_commands.describe(
    url="URL iCal directe optionnelle / Direct iCal URL",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def now_command(
    interaction: discord.Interaction,
    url: str | None = None,
) -> None:
    """Execute /now slash command."""
    await interaction.response.defer(ephemeral=False)

    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)

    target_url = url
    if not target_url:
        if profile and profile.ical_url:
            target_url = profile.ical_url
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

    try:
        current_course, upcoming = await get_next_classes(target_url, limit=4)
        embed = create_now_embed(current_course, upcoming, lang=lang)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error executing /now: {e}", exc_info=True)
        err_msg = (
            "⚠️ An error occurred while fetching live courses."
            if lang == "en"
            else "⚠️ Une erreur est survenue lors de la récupération des cours en direct."
        )
        await interaction.followup.send(err_msg, ephemeral=True)
