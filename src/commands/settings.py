"""Slash command: /settings to configure iCal URL, reminders, and format."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

from database import (
    delete_user_profile,
    get_user_profile,
    register_user_ical,
    update_user_notifications,
)
from services.ical_service import fetch_ical_content

logger = logging.getLogger(__name__)


@app_commands.command(
    name="settings",
    description="Gérer vos paramètres et votre lien d'emploi du temps EPSI Hyperplanning",
)
@app_commands.describe(
    register="Enregistrer ou mettre à jour votre URL iCal Hyperplanning",
    unregister="Supprimer votre compte et données enregistrées",
    daily="Activer/Désactiver le rappel quotidien à 06:00",
    weekly="Activer/Désactiver le rappel hebdomadaire chaque lundi à 06:00",
    default_format="Format d'affichage préféré par défaut",
)
@app_commands.choices(
    daily=[
        app_commands.Choice(name="Activer", value="Activer"),
        app_commands.Choice(name="Désactiver", value="Désactiver"),
    ],
    weekly=[
        app_commands.Choice(name="Activer", value="Activer"),
        app_commands.Choice(name="Désactiver", value="Désactiver"),
    ],
    default_format=[
        app_commands.Choice(name="Image (visuel dynamique)", value="image"),
        app_commands.Choice(name="Embed (texte)", value="embed"),
    ],
    unregister=[
        app_commands.Choice(name="Supprimer mes données", value="confirm"),
    ],
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def settings_command(
    interaction: discord.Interaction,
    register: str | None = None,
    unregister: str | None = None,
    daily: str | None = None,
    weekly: str | None = None,
    default_format: str | None = None,
) -> None:
    """Manage user preferences."""
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id

    if unregister == "confirm":
        success = await delete_user_profile(user_id)
        if success:
            await interaction.followup.send(
                "🗑️ Vos informations et votre lien iCal ont été supprimés avec succès.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "ℹ️ Vous n'étiez pas enregistré dans la base de données.",
                ephemeral=True,
            )
        return

    updates_made = []

    if register:
        # Validate that URL is reachable and looks like an iCal
        if not (register.startswith("http://") or register.startswith("https://")):
            await interaction.followup.send(
                "❌ **Lien iCal invalide.** L'adresse doit commencer par `http://` ou `https://`.",
                ephemeral=True,
            )
            return

        try:
            content = await fetch_ical_content(register, force_refresh=True)
            if "BEGIN:VCALENDAR" not in content:
                await interaction.followup.send(
                    "⚠️ Le lien fourni ne semble pas être un fichier calendrier iCal valide (pas de balise VCALENDAR).",
                    ephemeral=True,
                )
                return
        except Exception as e:
            await interaction.followup.send(
                f"❌ Impossible d'accéder au lien iCal spécifié : {e}",
                ephemeral=True,
            )
            return

        profile = await register_user_ical(user_id, register)
        updates_made.append("✅ **Lien iCal Hyperplanning enregistré avec succès !**")

    # Fetch updated or current profile
    profile = await get_user_profile(user_id)

    if daily is not None:
        if not profile:
            await interaction.followup.send(
                "❌ Veuillez d'abord enregistrer votre lien iCal avec `/settings register:` avant de configurer les notifications.",
                ephemeral=True,
            )
            return
        is_daily = daily == "Activer"
        await update_user_notifications(user_id, daily=is_daily)
        status_str = "activé" if is_daily else "désactivé"
        updates_made.append(f"⏰ Rappel quotidien : **{status_str}**")

    if weekly is not None:
        if not profile:
            await interaction.followup.send(
                "❌ Veuillez d'abord enregistrer votre lien iCal avec `/settings register:` avant de configurer les notifications.",
                ephemeral=True,
            )
            return
        is_weekly = weekly == "Activer"
        await update_user_notifications(user_id, weekly=is_weekly)
        status_str = "activé" if is_weekly else "désactivé"
        updates_made.append(f"📆 Rappel hebdomadaire : **{status_str}**")

    if default_format is not None:
        if not profile:
            await interaction.followup.send(
                "❌ Veuillez d'abord enregistrer votre lien iCal avec `/settings register:` avant de modifier vos préférences.",
                ephemeral=True,
            )
            return
        is_image = default_format == "image"
        await update_user_notifications(user_id, prefer_image=is_image)
        updates_made.append(
            f"🎨 Format d'affichage par défaut : **{'Image' if is_image else 'Embed texte'}**"
        )

    # If no options were passed, display current settings
    profile = await get_user_profile(user_id)
    embed = discord.Embed(
        title="⚙️ Paramètres de votre compte EPSI Bot",
        color=discord.Color.blue(),
    )

    if profile:
        url_val = profile.ical_url or ""
        ical_display = (
            f"`{url_val[:45]}...`"
            if len(url_val) > 45
            else (f"`{url_val}`" if url_val else "Non configuré")
        )
        embed.add_field(name="🔗 Lien iCal enregistré", value=ical_display, inline=False)
        embed.add_field(
            name="⏰ Rappel quotidien (06:00)",
            value="🟢 Activé" if profile.daily_notifications else "🔴 Désactivé",
            inline=True,
        )
        embed.add_field(
            name="📆 Rappel hebdo (Lundi 06:00)",
            value="🟢 Activé" if profile.weekly_notifications else "🔴 Désactivé",
            inline=True,
        )
        embed.add_field(
            name="🎨 Format d'affichage",
            value="🖼️ Image" if profile.prefer_image else "📄 Embed texte",
            inline=True,
        )
    else:
        embed.description = (
            "Vous n'avez pas encore configuré votre emploi du temps.\n\n"
            "👉 Utilisez `/settings register <votre_lien_ical>` pour lier votre Hyperplanning !"
        )

    response_text = "\n".join(updates_made) if updates_made else ""
    if response_text:
        await interaction.followup.send(content=response_text, embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)
