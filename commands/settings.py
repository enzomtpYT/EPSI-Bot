import discord
from discord import app_commands
import logging
from lib.user_manager import get_user, set_user, set_user_preference, get_user_preference

@discord.app_commands.command(
    name="settings",
    description="Gérer vos paramètres"
)
@app_commands.describe(daily="Activer/Désactiver les notifications quotidiennes", weekly="Activer/Désactiver les notifications hebdomadaires", register="Enregistrer votre nom d'utilisateur EPSI", unregister="Supprimer votre enregistrement")
@app_commands.choices(
    daily=[
        app_commands.Choice(name="Activer", value="Activer"),
        app_commands.Choice(name="Désactiver", value="Désactiver")
    ],
    weekly=[
        app_commands.Choice(name="Activer", value="Activer"),
        app_commands.Choice(name="Désactiver", value="Désactiver")
    ],
    unregister=[
        app_commands.Choice(name="Désenregistrer", value="Désenregistrer")
    ]
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def settings(interaction: discord.Interaction, daily: str = None, weekly: str = None, register: str = None, unregister: str = None):
    logging.info(f"Commande /settings exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    
    await interaction.response.defer(ephemeral=True)
    
    user_id = interaction.user.id
    username = get_user(user_id)
    
    if unregister:
        if username:
            from lib.user_manager import remove_user
            remove_user(user_id)
            await interaction.followup.send("Votre enregistrement a été supprimé avec succès.", ephemeral=True)
            logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) désenregistré.")
        else:
            await interaction.followup.send("Vous n'êtes pas enregistré.", ephemeral=True)
        return
    
    if register:
        if username:
            set_user(user_id, register)
            msg = await interaction.followup.send(f"Votre nom d'utilisateur a été mis à jour avec succès : {register}", ephemeral=True)
            logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) a mis à jour son nom d'utilisateur : {register}")
        else:
            username = register
            set_user(user_id, register)
            msg = await interaction.followup.send(f"Votre nom d'utilisateur a été enregistré avec succès : {register}", ephemeral=True)
            logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) enregistré avec le nom d'utilisateur: {register}")
    
    if not username:
        await interaction.followup.send("Vous devez d'abord vous enregistrer en utilisant la commande `/settings register` avant de gérer vos paramètres.", ephemeral=True)
        return
    
    response_messages = []
    
    if daily is not None:
        daily_bool = daily == "Activer"
        if set_user_preference(user_id, "daily", daily_bool):
            status = "activées" if daily_bool else "désactivées"
            response_messages.append(f"Notifications quotidiennes {status}.")
            logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) a {status} les notifications quotidiennes.")
        else:
            response_messages.append("Erreur lors de la mise à jour des notifications quotidiennes.")
    
    if weekly is not None:
        weekly_bool = weekly == "Activer"
        if set_user_preference(user_id, "weekly", weekly_bool):
            status = "activées" if weekly_bool else "désactivées"
            response_messages.append(f"Notifications hebdomadaires {status}.")
            logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) a {status} les notifications hebdomadaires.")
        else:
            response_messages.append("Erreur lors de la mise à jour des notifications hebdomadaires.")
    
    # Show current settings if no changes were made
    if not response_messages and not register:
        daily_pref = get_user_preference(user_id, "daily")
        weekly_pref = get_user_preference(user_id, "weekly")
        
        daily_status = "activées" if daily_pref else "désactivées"
        weekly_status = "activées" if weekly_pref else "désactivées"
        
        response_messages.append(f"**Paramètres actuels :**")
        response_messages.append(f"• Notifications quotidiennes : {daily_status}")
        response_messages.append(f"• Notifications hebdomadaires : {weekly_status}")

    if response_messages:
        content_to_add = "\n\n" + "\n".join(response_messages)
        try:
            if 'msg' in locals() and msg is not None:
                # Some channels/contexts may not allow editing interaction followups; fall back to send on failure
                try:
                    await msg.edit(content=(msg.content or "") + content_to_add)
                except Exception:
                    await interaction.followup.send("\n".join(response_messages), ephemeral=True)
            else:
                await interaction.followup.send("\n".join(response_messages), ephemeral=True)
        except Exception as e:
            logging.exception("Failed to deliver settings response")