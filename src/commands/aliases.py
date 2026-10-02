"""Command aliases: /daily and /weekly matching /day and /week."""

from __future__ import annotations

import discord
from discord import app_commands

from commands.day import handle_day_command
from commands.week import handle_week_command


@app_commands.command(
    name="daily",
    description="Afficher l'emploi du temps pour une journée (alias /day) / View daily schedule",
)
@app_commands.describe(
    date="Date au format JJ/MM/AAAA (ex: 15/10/2026) / Date DD/MM/YYYY",
    image="Afficher sous forme d'image ou d'embed / Image or Text embed",
    url="URL iCal directe optionnelle / Direct iCal URL",
    user="Utilisateur dont vous souhaitez voir l'emploi du temps / User whose schedule to view",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def daily_command(
    interaction: discord.Interaction,
    date: str | None = None,
    image: bool | None = None,
    url: str | None = None,
    user: discord.User | None = None,
) -> None:
    """Execute /daily alias."""
    await handle_day_command(interaction, date=date, image=image, url=url, user=user)


@app_commands.command(
    name="weekly",
    description="Afficher l'emploi du temps pour la semaine (alias /week) / View weekly schedule",
)
@app_commands.describe(
    date="Date comprise dans la semaine au format JJ/MM/AAAA / Date DD/MM/YYYY",
    image="Afficher sous forme de calendrier image ou d'embed / Image or Text embed",
    url="URL iCal directe optionnelle / Direct iCal URL",
    user="Utilisateur dont vous souhaitez voir l'emploi du temps / User whose schedule to view",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def weekly_command(
    interaction: discord.Interaction,
    date: str | None = None,
    image: bool | None = None,
    url: str | None = None,
    user: discord.User | None = None,
) -> None:
    """Execute /weekly alias."""
    await handle_week_command(interaction, date=date, image=image, url=url, user=user)
