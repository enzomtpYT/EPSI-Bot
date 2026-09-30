"""Bot setup and slash command registration."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from commands.day import day_command
from commands.now import now_command
from commands.settings import settings_command
from commands.week import week_command

logger = logging.getLogger(__name__)


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot client with slash commands."""
    intents = discord.Intents.default()
    intents.dm_messages = True

    bot = commands.Bot(command_prefix=[], intents=intents)

    # Register slash commands to the command tree
    bot.tree.add_command(day_command)
    bot.tree.add_command(week_command)
    bot.tree.add_command(now_command)
    bot.tree.add_command(settings_command)

    return bot
