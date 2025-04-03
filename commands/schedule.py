import discord
from discord import app_commands
import logging
import io
from lib.api import fetch_schedule
from lib.schedule_utils import create_schedule_embed, create_schedule_image
from lib.user_manager import get_user

@discord.app_commands.command(
    name="edt",
    description="Obtenir votre emploi du temps EPSI"
)
@app_commands.describe(
    username="Nom d'utilisateur EPSI (optionnel si vous êtes enregistré)",
    start_time="Date de début au format JJ/MM/AAAA (optionnel)",
    end_time="Date de fin au format JJ/MM/AAAA (optionnel)",
    image="Si activé, envoie l'emploi du temps sous forme d'image"
)
@app_commands.user_install()
async def schedule(
    interaction: discord.Interaction, 
    username: str = None, 
    start_time: str = None, 
    end_time: str = None,
    image: bool = False
):
    logging.info(f"Commande /edt exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    logging.info(f"Paramètres: username={username}, start_time={start_time}, end_time={end_time}, image={image}")
    
    await interaction.response.defer()

    # If no username provided, check if user is registered
    if username is None:
        username = get_user(interaction.user.id)
        if not username:
            logging.warning(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) non enregistré")
            await interaction.followup.send("Merci d'enregistrer votre nom d'utilisateur avec la commande `/register` ou de spécifier un nom d'utilisateur directement.", ephemeral=True)
            return
        logging.info(f"Utilisation du nom d'utilisateur enregistré: {username}")
    
    schedule_data = await fetch_schedule(username, start_time, end_time)
    logging.info(f"Nombre de cours trouvés: {len(schedule_data)}")
    
    if image:
        # Generate and send images
        images = create_schedule_image(schedule_data)
        files = []
        for i, img in enumerate(images):
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Create discord file
            file = discord.File(img_byte_arr, filename=f'schedule_page_{i+1}.png')
            files.append(file)
        
        await interaction.followup.send(files=files, ephemeral=True)
        logging.info(f"Image(s) envoyée(s) à {interaction.user.name}")
    else:
        # Send embed as before
        embed = create_schedule_embed(schedule_data)
        await interaction.followup.send(embed=embed, ephemeral=True)
        logging.info(f"Embed envoyé à {interaction.user.name}") 