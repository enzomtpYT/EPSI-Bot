import discord
from discord import app_commands
import logging
from lib.user_manager import get_user, remove_user

@discord.app_commands.command(
    name="unregister",
    description="Supprimer votre enregistrement EPSI"
)
async def unregister(interaction: discord.Interaction):
    logging.info(f"Commande /unregister exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    
    await interaction.response.defer(ephemeral=True)
    
    # Check if user is registered
    if not get_user(interaction.user.id):
        logging.warning(f"Tentative de désenregistrement par {interaction.user.name} (ID: {interaction.user.id}) qui n'est pas enregistré")
        await interaction.followup.send("Vous n'êtes pas enregistré.", ephemeral=True)
        return
    
    # Remove the user
    if remove_user(interaction.user.id):
        await interaction.followup.send("Votre enregistrement a été supprimé avec succès.", ephemeral=True)
        logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) désenregistré")
    else:
        await interaction.followup.send("Une erreur est survenue lors de la suppression de votre enregistrement.", ephemeral=True)
        logging.error(f"Erreur lors de la désinscription de {interaction.user.name} (ID: {interaction.user.id})") 