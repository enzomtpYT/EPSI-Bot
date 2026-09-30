"""Slash command: /settings to configure iCal URL, reminders, format, and language."""

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
from services.i18n import resolve_user_language, t
from services.ical_service import fetch_ical_content

logger = logging.getLogger(__name__)


@app_commands.command(
    name="settings",
    description="Gérer vos paramètres et votre lien d'emploi du temps EPSI Hyperplanning / Manage your settings",
)
@app_commands.describe(
    register="Enregistrer ou mettre à jour votre URL iCal Hyperplanning / Register iCal URL",
    unregister="Supprimer votre compte et données enregistrées / Delete registered data",
    daily="Activer/Désactiver le rappel quotidien à 06:00 / Daily reminder toggle",
    weekly="Activer/Désactiver le rappel hebdomadaire chaque lundi à 06:00 / Weekly reminder toggle",
    work_days="Afficher les jours en entreprise (Alternance) / Show company work days",
    default_format="Format d'affichage préféré par défaut / Default display format",
    language="Langue du bot / Bot language (Français / English)",
)
@app_commands.choices(
    daily=[
        app_commands.Choice(name="Activer / Enable", value="Activer"),
        app_commands.Choice(name="Désactiver / Disable", value="Désactiver"),
    ],
    weekly=[
        app_commands.Choice(name="Activer / Enable", value="Activer"),
        app_commands.Choice(name="Désactiver / Disable", value="Désactiver"),
    ],
    work_days=[
        app_commands.Choice(name="Activer / Enable", value="Activer"),
        app_commands.Choice(name="Désactiver / Disable", value="Désactiver"),
    ],
    default_format=[
        app_commands.Choice(name="🖼️ Image", value="image"),
        app_commands.Choice(name="📄 Embed texte / Text", value="embed"),
    ],
    language=[
        app_commands.Choice(name="🇫🇷 Français", value="fr"),
        app_commands.Choice(name="🇬🇧 English", value="en"),
    ],
    unregister=[
        app_commands.Choice(name="Supprimer mes données / Delete my data", value="confirm"),
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
    work_days: str | None = None,
    default_format: str | None = None,
    language: str | None = None,
) -> None:
    """Manage user preferences."""
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    current_profile = await get_user_profile(user_id)

    # Initial language resolution
    lang = resolve_user_language(interaction, current_profile)
    if language is not None:
        lang = language

    if unregister == "confirm":
        success = await delete_user_profile(user_id)
        if success:
            await interaction.followup.send(
                t("settings_deleted", lang=lang),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                t("settings_not_found", lang=lang),
                ephemeral=True,
            )
        return

    updates_made = []

    if register:
        if not (
            register.startswith("http://")
            or register.startswith("https://")
            or register.startswith("webcal://")
        ):
            await interaction.followup.send(
                t("settings_invalid_url", lang=lang),
                ephemeral=True,
            )
            return

        normalized_url = register
        if normalized_url.startswith("webcal://"):
            normalized_url = "https://" + normalized_url[len("webcal://") :]

        try:
            content = await fetch_ical_content(normalized_url, force_refresh=True)
            if "BEGIN:VCALENDAR" not in content:
                await interaction.followup.send(
                    t("settings_invalid_ical", lang=lang),
                    ephemeral=True,
                )
                return
        except Exception as e:
            await interaction.followup.send(
                t("settings_access_error", lang=lang, error=str(e)),
                ephemeral=True,
            )
            return

        current_profile = await register_user_ical(user_id, normalized_url)
        updates_made.append(t("settings_url_saved", lang=lang))

    # Fetch updated profile
    current_profile = await get_user_profile(user_id)

    if language is not None:
        if not current_profile:
            await interaction.followup.send(
                t("settings_must_register", lang=lang),
                ephemeral=True,
            )
            return
        await update_user_notifications(user_id, language=language)
        lang = language
        lang_str = (
            t("settings_language_val_en", lang=lang)
            if language == "en"
            else t("settings_language_val_fr", lang=lang)
        )
        updates_made.append(t("settings_lang_updated", lang=lang, language=lang_str))

    if daily is not None:
        if not current_profile:
            await interaction.followup.send(
                t("settings_must_register", lang=lang),
                ephemeral=True,
            )
            return
        is_daily = daily == "Activer"
        await update_user_notifications(user_id, daily=is_daily)
        status_key = "status_activated" if is_daily else "status_deactivated"
        updates_made.append(t("settings_daily_updated", lang=lang, status=t(status_key, lang=lang)))

    if weekly is not None:
        if not current_profile:
            await interaction.followup.send(
                t("settings_must_register", lang=lang),
                ephemeral=True,
            )
            return
        is_weekly = weekly == "Activer"
        await update_user_notifications(user_id, weekly=is_weekly)
        status_key = "status_activated" if is_weekly else "status_deactivated"
        updates_made.append(
            t("settings_weekly_updated", lang=lang, status=t(status_key, lang=lang))
        )

    if work_days is not None:
        if not current_profile:
            await interaction.followup.send(
                t("settings_must_register", lang=lang),
                ephemeral=True,
            )
            return
        is_work = work_days == "Activer"
        await update_user_notifications(user_id, show_work_days=is_work)
        status_key = "status_activated" if is_work else "status_deactivated"
        updates_made.append(t("settings_work_updated", lang=lang, status=t(status_key, lang=lang)))

    if default_format is not None:
        if not current_profile:
            await interaction.followup.send(
                t("settings_must_register", lang=lang),
                ephemeral=True,
            )
            return
        is_image = default_format == "image"
        await update_user_notifications(user_id, prefer_image=is_image)
        fmt_key = "settings_format_img" if is_image else "settings_format_txt"
        updates_made.append(t("settings_format_updated", lang=lang, format=t(fmt_key, lang=lang)))

    # Display current settings embed
    current_profile = await get_user_profile(user_id)
    lang = resolve_user_language(interaction, current_profile)

    embed = discord.Embed(
        title=t("settings_title", lang=lang),
        color=discord.Color.blue(),
    )

    if current_profile:
        url_val = current_profile.ical_url or ""
        ical_display = (
            f"`{url_val[:45]}...`"
            if len(url_val) > 45
            else (
                f"`{url_val}`"
                if url_val
                else ("Not configured" if lang == "en" else "Non configuré")
            )
        )
        embed.add_field(name=t("settings_ical_field", lang=lang), value=ical_display, inline=False)

        daily_val = t(
            "settings_enabled" if current_profile.daily_notifications else "settings_disabled",
            lang=lang,
        )
        embed.add_field(name=t("settings_daily_field", lang=lang), value=daily_val, inline=True)

        weekly_val = t(
            "settings_enabled" if current_profile.weekly_notifications else "settings_disabled",
            lang=lang,
        )
        embed.add_field(name=t("settings_weekly_field", lang=lang), value=weekly_val, inline=True)

        work_val = t(
            "settings_enabled" if current_profile.show_work_days else "settings_disabled",
            lang=lang,
        )
        embed.add_field(name=t("settings_work_field", lang=lang), value=work_val, inline=True)

        format_val = t(
            "settings_format_img" if current_profile.prefer_image else "settings_format_txt",
            lang=lang,
        )
        embed.add_field(name=t("settings_format_field", lang=lang), value=format_val, inline=True)

        lang_val = t(
            "settings_language_val_en"
            if current_profile.language == "en"
            else "settings_language_val_fr",
            lang=lang,
        )
        embed.add_field(name=t("settings_language_field", lang=lang), value=lang_val, inline=True)
    else:
        embed.description = t("settings_not_configured", lang=lang)

    embed.set_footer(text=t("footer_epsi", lang=lang))

    response_text = "\n".join(updates_made) if updates_made else ""
    if response_text:
        await interaction.followup.send(content=response_text, embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)
