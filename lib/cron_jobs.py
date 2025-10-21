from lib.user_manager import get_users_with_preference
from lib.schedule_utils import day_schedule_image, week_schedule_image
from lib.api import fetch_day_schedule, fetch_week_schedule
import logging, time, io
import discord


async def run_daily_job(bot: discord.Client):
    """Run the daily job to send notifications to users with daily reminders enabled.

    Args:
        bot: The discord.py Bot/Client instance used to fetch users and send DMs.
    """

    users = get_users_with_preference("daily")
    logging.info(f"Lancement du travail quotidien pour {len(users)} utilisateur(s) avec des rappels quotidiens activés.")
    for user in users:
        try:
            # Fetch schedule data from the API
            schedule_data = await fetch_day_schedule(user.username, time.strftime("%d/%m/%Y"))

            # Generate image bytes
            success, result = day_schedule_image(schedule_data)

            if not success:
                logging.error(f"Erreur lors de la génération de l'image pour {user.username}: {result}")
                continue

            image_bytes = result

            # Prepare in-memory file
            bio = io.BytesIO(image_bytes)
            bio.seek(0)
            filename = f"emploi_du_temps_{user.id}.png"

            # Try to get the Discord user (from cache first, then via API)
            discord_user = bot.get_user(user.id)
            if discord_user is None:
                try:
                    discord_user = await bot.fetch_user(user.id)
                except Exception as e:
                    logging.exception(f"Impossible de récupérer l'utilisateur Discord {user.id}: {e}")
                    continue

            # Send DM with the image
            try:
                await discord_user.send(content="Voici l'emploi du temps du jour", file=discord.File(fp=bio, filename=filename))
                logging.info(f"Emploi du temps envoyé à {user.username} ({user.id})")
            except discord.Forbidden:
                logging.warning(f"Impossible d'envoyer un DM à {user.username} ({user.id}) : autorisation refusée")
            except Exception as e:
                logging.exception(f"Échec de l'envoi du DM à {user.username} ({user.id}) : {e}")

        except Exception as e:
            logging.exception(f"Erreur lors de la récupération de l'emploi du temps pour {user.username}: {e}")

async def run_weekly_job(bot: discord.Client):
    """Run the weekly job to send notifications to users with weekly reminders enabled.

    Args:
        bot: The discord.py Bot/Client instance used to fetch users and send DMs.
    """

    users = get_users_with_preference("weekly")
    logging.info(f"Lancement du travail hebdomadaire pour {len(users)} utilisateur(s) avec des rappels hebdomadaires activés.")
    for user in users:
        try:
            # Fetch weekly schedule data from the API
            schedule_data = await fetch_week_schedule(user.username, time.strftime("%d/%m/%Y"))

            # Generate image bytes for the week
            success, result = week_schedule_image(schedule_data)

            if not success:
                logging.error(f"Erreur lors de la génération de l'image (semaine) pour {user.username}: {result}")
                continue

            image_bytes = result

            # Prepare in-memory file
            bio = io.BytesIO(image_bytes)
            bio.seek(0)
            filename = f"emploi_semaine_{user.id}.png"

            # Try to get the Discord user (from cache first, then via API)
            discord_user = bot.get_user(user.id)
            if discord_user is None:
                try:
                    discord_user = await bot.fetch_user(user.id)
                except Exception as e:
                    logging.exception(f"Impossible de récupérer l'utilisateur Discord {user.id}: {e}")
                    continue

            # Send DM with the image
            try:
                await discord_user.send(content="Voici l'emploi du temps de la semaine", file=discord.File(fp=bio, filename=filename))
                logging.info(f"Emploi du temps (semaine) envoyé à {user.username} ({user.id})")
            except discord.Forbidden:
                logging.warning(f"Impossible d'envoyer un DM à {user.username} ({user.id}) : autorisation refusée")
            except Exception as e:
                logging.exception(f"Échec de l'envoi du DM à {user.username} ({user.id}) : {e}")

        except Exception as e:
            logging.exception(f"Erreur lors de la récupération de l'emploi du temps (semaine) pour {user.username}: {e}")
