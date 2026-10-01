"""Slash command group: /share to manage schedule whitelist and share links."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

from config import settings
from database import (
    add_whitelisted_viewer,
    generate_or_get_share_token,
    get_user_profile,
    get_whitelisted_viewers,
    remove_whitelisted_viewer,
    toggle_sharing,
)
from services.i18n import resolve_user_language

logger = logging.getLogger(__name__)


class ShareGroup(app_commands.Group):
    """Command group for schedule sharing permissions."""

    def __init__(self) -> None:
        super().__init__(
            name="share",
            description="Gérer le partage d'emploi du temps / Manage schedule sharing and whitelist",
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
            default_permissions=None,
        )


share_group = ShareGroup()


@share_group.command(
    name="allow",
    description="Autoriser un utilisateur à voir votre emploi du temps / Allow a user to view your schedule",
)
@app_commands.describe(user="L'utilisateur Discord à autoriser / Discord user to whitelist")
async def share_allow(interaction: discord.Interaction, user: discord.User) -> None:
    """Add user to schedule whitelist."""
    await interaction.response.defer(ephemeral=True)
    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)

    if user.id == interaction.user.id:
        msg = (
            "ℹ️ You already have access to your own schedule!"
            if lang == "en"
            else "ℹ️ Vous avez déjà accès à votre propre emploi du temps !"
        )
        await interaction.followup.send(msg, ephemeral=True)
        return

    # Enable sharing if not enabled
    await toggle_sharing(interaction.user.id, True)
    added = await add_whitelisted_viewer(owner_id=interaction.user.id, viewer_id=user.id)

    if added:
        msg = (
            f"✅ **{user.mention} is now authorized!**\n"
            f"They can view your schedule using `/day user:{interaction.user.mention}` or on the WebUI."
            if lang == "en"
            else f"✅ **{user.mention} est désormais autorisé(e) !**\n"
            f"Il/Elle peut consulter votre emploi du temps avec `/day user:{interaction.user.mention}` ou sur le Web."
        )
    else:
        msg = (
            f"ℹ️ {user.mention} was already in your whitelist."
            if lang == "en"
            else f"ℹ️ {user.mention} est déjà dans votre liste d'utilisateurs autorisés."
        )
    await interaction.followup.send(msg, ephemeral=True)


@share_group.command(
    name="revoke",
    description="Retirer l'accès à un utilisateur / Revoke schedule access for a user",
)
@app_commands.describe(user="L'utilisateur à retirer / Discord user to remove")
async def share_revoke(interaction: discord.Interaction, user: discord.User) -> None:
    """Remove user from schedule whitelist."""
    await interaction.response.defer(ephemeral=True)
    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)

    removed = await remove_whitelisted_viewer(owner_id=interaction.user.id, viewer_id=user.id)
    if removed:
        msg = (
            f"🚫 **Access revoked**: {user.mention} can no longer view your schedule."
            if lang == "en"
            else f"🚫 **Accès retiré** : {user.mention} ne peut plus consulter votre emploi du temps."
        )
    else:
        msg = (
            f"ℹ️ {user.mention} was not in your whitelist."
            if lang == "en"
            else f"ℹ️ {user.mention} n'était pas dans votre liste autorisée."
        )
    await interaction.followup.send(msg, ephemeral=True)


@share_group.command(
    name="list",
    description="Voir la liste des personnes autorisées / View your sharing whitelist",
)
async def share_list(interaction: discord.Interaction) -> None:
    """List whitelisted users."""
    await interaction.response.defer(ephemeral=True)
    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)

    viewer_ids = await get_whitelisted_viewers(interaction.user.id)
    status_label = (
        ("🟢 Enabled" if lang == "en" else "🟢 Activé")
        if (profile and profile.share_enabled)
        else ("🔴 Disabled" if lang == "en" else "🔴 Désactivé")
    )

    if not viewer_ids:
        msg = (
            f"📋 **Schedule Sharing ({status_label})**\n\n"
            "You have not authorized anyone yet.\n"
            "Use `/share allow @user` to whitelist a Discord user."
            if lang == "en"
            else f"📋 **Partage d'emploi du temps ({status_label})**\n\n"
            "Aucun utilisateur n'est actuellement autorisé.\n"
            "Utilisez `/share allow @utilisateur` pour ajouter quelqu'un."
        )
        await interaction.followup.send(msg, ephemeral=True)
        return

    users_text = "\n".join(f"• <@{vid}> (`{vid}`)" for vid in viewer_ids)
    msg = (
        f"📋 **Schedule Sharing Whitelist ({status_label})**\n\n"
        f"The following {len(viewer_ids)} user(s) can view your schedule:\n"
        f"{users_text}\n\n"
        "To revoke access: `/share revoke @user`"
        if lang == "en"
        else f"📋 **Utilisateurs autorisés ({status_label})**\n\n"
        f"Les {len(viewer_ids)} utilisateur(s) suivant(s) peuvent consulter votre emploi du temps :\n"
        f"{users_text}\n\n"
        "Pour retirer un accès : `/share revoke @utilisateur`"
    )
    await interaction.followup.send(msg, ephemeral=True)


@share_group.command(
    name="link",
    description="Obtenir ou régénérer votre lien secret de partage Web / View or reset your web share link",
)
@app_commands.describe(
    regenerate="Générer un nouveau lien et invalider le précédent / Generate a new link and revoke old one"
)
async def share_link(interaction: discord.Interaction, regenerate: bool = False) -> None:
    """View or regenerate web share link."""
    await interaction.response.defer(ephemeral=True)
    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)

    token = await generate_or_get_share_token(interaction.user.id, force_new=regenerate)
    base_url = (
        settings.discord_redirect_uri.split("/auth/callback")[0]
        if settings.discord_redirect_uri
        else "http://localhost:8080"
    )
    share_url = f"{base_url}/share/{token}"

    msg = (
        f"🔗 **Your Secret Web Share Link**\n\n"
        f"<{share_url}>\n\n"
        "Anyone with this link can view your schedule on the web without logging in.\n"
        "To reset this link at any time, run `/share link regenerate:True`."
        if lang == "en"
        else f"🔗 **Votre lien secret de partage Web**\n\n"
        f"<{share_url}>\n\n"
        "Toute personne disposant de ce lien peut voir votre emploi du temps sur le web sans compte.\n"
        "Pour révoquer ce lien à tout moment, tapez `/share link regenerate:True`."
    )
    await interaction.followup.send(msg, ephemeral=True)


@share_group.command(
    name="toggle",
    description="Activer ou désactiver le partage de votre emploi du temps / Enable or disable schedule sharing",
)
@app_commands.describe(enabled="Activer ou désactiver / Enable or disable")
async def share_toggle(interaction: discord.Interaction, enabled: bool) -> None:
    """Enable or disable schedule sharing."""
    await interaction.response.defer(ephemeral=True)
    profile = await get_user_profile(interaction.user.id)
    lang = resolve_user_language(interaction, profile)

    await toggle_sharing(interaction.user.id, enabled)
    if enabled:
        msg = (
            "🟢 **Schedule sharing is now ENABLED.**\n"
            "Whitelisted users and people with your secret link can view your schedule."
            if lang == "en"
            else "🟢 **Le partage d'emploi du temps est désormais ACTIVÉ.**\n"
            "Les utilisateurs autorisés et personnes avec votre lien secret peuvent voir votre planning."
        )
    else:
        msg = (
            "🔴 **Schedule sharing is now DISABLED.**\n"
            "Nobody can view your schedule until you re-enable it."
            if lang == "en"
            else "🔴 **Le partage d'emploi du temps est désormais DÉSACTIVÉ.**\n"
            "Personne ne peut consulter votre emploi du temps tant que le partage est éteint."
        )
    await interaction.followup.send(msg, ephemeral=True)
