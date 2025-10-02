import discord
from discord import app_commands
import logging
import io
from lib.api import fetch_week_schedule
from lib.schedule_utils import create_schedule_embed, week_schedule_image
from lib.user_manager import get_user
from datetime import datetime

@discord.app_commands.command(
    name="week",
    description="Obtenir votre emploi du temps EPSI pour une semaine complète"
)
@app_commands.describe(
    username="Nom d'utilisateur EPSI (optionnel si vous êtes enregistré)",
    date="Date au format JJ/MM/AAAA (optionnel, utilise la date du jour pour trouver la semaine actuelle)",
    image="Si activé, envoie l'emploi du temps sous forme d'image"
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def week(
    interaction: discord.Interaction, 
    username: str = None, 
    date: str = None,
    image: bool = True
):
    logging.info(f"Commande /week exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    logging.info(f"Paramètres: username={username}, date={date}, image={image}")
    
    await interaction.response.defer()

    # If no username provided, check if user is registered
    if username is None:
        username = get_user(interaction.user.id)
        if not username:
            logging.warning(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) non enregistré")
            await interaction.followup.send("Merci d'enregistrer votre nom d'utilisateur avec la commande `/register` ou de spécifier un nom d'utilisateur directement.", ephemeral=True)
            return
        logging.info(f"Utilisation du nom d'utilisateur enregistré: {username}")
    
    # Validate date format if provided
    if date:
        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            logging.error(f"Format de date invalide: {date}")
            await interaction.followup.send("Format de date invalide. Veuillez utiliser le format JJ/MM/AAAA.", ephemeral=True)
            return
    
    try:
        schedule_data = await fetch_week_schedule(username, date)
        logging.info(f"Nombre de cours trouvés: {len(schedule_data)}")
        
        if not schedule_data:
            await interaction.followup.send("Aucun cours trouvé pour la semaine spécifiée.", ephemeral=True)
            return
            
        if image:
            success, result = week_schedule_image(schedule_data)
            if not success:
                logging.error(f"Erreur lors de la génération de l'image: {result}")
                await interaction.followup.send("Une erreur est survenue lors de la génération de l'image de l'emploi du temps.", ephemeral=True)
                return
            
            image_bytes = io.BytesIO(result)
            image_bytes.seek(0)
            file = discord.File(fp=image_bytes, filename="week_schedule.png")
            files = [file]
            
            await interaction.followup.send(files=files, ephemeral=True)
            logging.info(f"Image(s) envoyée(s) à {interaction.user.name}")
        else:
            # Send embed
            embed = create_schedule_embed(schedule_data)
            await interaction.followup.send(embed=embed, ephemeral=True)
            logging.info(f"Embed envoyé à {interaction.user.name}")
    except Exception as e:
        error_message = "Une erreur est survenue lors de la récupération de l'emploi du temps. Veuillez réessayer plus tard."
        logging.error(f"Erreur lors de la récupération de l'emploi du temps: {str(e)}")
        await interaction.followup.send(error_message, ephemeral=True)