"""Slash command: /now to check current class and upcoming classes."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

from database import get_user_profile
from services.embed_builder import create_now_embed
from services.ical_service import get_next_classes

logger = logging.getLogger(__name__)


@app_commands.command(
    name="now",
    description="Afficher le cours en cours et les prochains cours à venir",
)
@app_commands.describe(
    url="URL iCal directe optionnelle (si non enregistré)",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def now_command(
    interaction: discord.Interaction,
    url: str | None = None,
) -> None:
    """Execute /now slash command."""
    await interaction.response.defer(ephemeral=False)

    target_url = url
    if not target_url:
        profile = await get_user_profile(interaction.user.id)
        if profile and profile.ical_url:
            target_url = profile.ical_url
        else:
            await interaction.followup.send(
                "❌ **Vous n'avez pas encore enregistré votre lien iCal !**\n"
                "Utilisez la commande `/settings register <votre_lien_ical>` pour lier votre emploi du temps "
                "ou passez le paramètre `url:` dans la commande.",
                ephemeral=True,
            )
            return

    try:
        current_course, upcoming = await get_next_classes(target_url, limit=4)
        embed = create_now_embed(current_course, upcoming)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error executing /now: {e}", exc_info=True)
        await interaction.followup.send(
            "⚠️ Une erreur est survenue lors de la récupération des cours en direct.",
            ephemeral=True,
        )
