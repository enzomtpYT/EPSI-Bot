import discord
from discord import app_commands
import logging
from lib.user_manager import get_user, set_user

@discord.app_commands.command(
    name="register",
    description="Enregistrer votre nom d'utilisateur EPSI"
)
@app_commands.describe(username="Votre nom d'utilisateur EPSI")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def register(interaction: discord.Interaction, username: str):
    logging.info(f"Commande /register exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    logging.info(f"Nom d'utilisateur à enregistrer: {username}")
    
    await interaction.response.defer(ephemeral=True)
    
    # Check if user is already registered
    if get_user(interaction.user.id):
        logging.warning(f"Tentative de réenregistrement par {interaction.user.name} (ID: {interaction.user.id})")
        await interaction.followup.send("Vous êtes déjà enregistré. Pour changer votre nom d'utilisateur, utilisez la commande `/unregister` d'abord.", ephemeral=True)
        return
    
    # Save the username
    set_user(interaction.user.id, username)
    
    await interaction.followup.send(f"Votre nom d'utilisateur a été enregistré avec succès : {username}", ephemeral=True)
    logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) enregistré avec le nom d'utilisateur: {username}") 