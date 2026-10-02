"""Main application entrypoint for EPSI Discord Bot."""

from __future__ import annotations

import asyncio
import logging
import sys

import aiocron

from bot import create_bot
from config import settings
from database import init_db
from tasks.cron_jobs import (
    run_daily_notification_job,
    run_weekly_notification_job,
)
from web.server import create_uvicorn_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("epsibot")

bot = create_bot()


@bot.event
async def on_ready() -> None:
    """Triggered when the Discord bot connection is established."""
    if bot.user:
        logger.info(f"Bot connected successfully as {bot.user.name} ({bot.user.id})")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synchronized {len(synced)} application slash command(s).")
    except Exception as e:
        logger.error(f"Failed to synchronize application commands: {e}")

    # Register daily cron at 06:00
    @aiocron.crontab("0 6 * * *")
    async def daily_cron() -> None:
        await run_daily_notification_job(bot)

    # Register weekly cron on Monday at 06:00
    @aiocron.crontab("0 6 * * 1")
    async def weekly_cron() -> None:
        await run_weekly_notification_job(bot)

    logger.info("Cron jobs for daily and weekly notifications registered.")


async def main() -> None:
    """Async main routine."""
    logger.info("Starting EPSI Bot v2.0...")
    await init_db()

    web_server = create_uvicorn_server()
    logger.info(f"Serving WebUI on http://{settings.web_host}:{settings.web_port}")

    token = settings.discord_token.strip().strip("'\"")
    if not token or token == "YOUR_DISCORD_TOKEN":
        logger.warning("No valid DISCORD_TOKEN found in environment. Starting WebUI standalone...")
        await web_server.serve()
        return

    async with bot:
        await asyncio.gather(
            bot.start(token),
            web_server.serve(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
