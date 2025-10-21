import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from lib.user_manager import load_users
from lib.cron_jobs import run_daily_job, run_weekly_job
from commands import day, week, settings
import aiocron

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.dm_messages = True
bot = commands.Bot(command_prefix=None, intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Bot prêt ! Connecté en tant que {bot.user.name} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synchronisation de {len(synced)} commande(s)")
    except Exception as e:
        logging.error(f"Échec de la synchronisation des commandes : {e}")

    @aiocron.crontab('0 6 * * *')  # Every day at 6 AM
    async def daily_cronjob():
        await run_daily_job(bot)

    # Weekly job: send weekly schedules (every Monday at 06:00)
    @aiocron.crontab('0 6 * * 1')
    async def weekly_cronjob():
        await run_weekly_job(bot)

# Load users when bot starts
load_users()

# Add commands to the bot
bot.tree.add_command(day.day)
bot.tree.add_command(week.week)
bot.tree.add_command(settings.settings)

# Get the token from environment variables
bot.run(os.getenv('DISCORD_TOKEN'))
