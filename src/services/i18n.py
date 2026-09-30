"""Internationalization and localization helper for EPSI Bot."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import discord

    from models import UserProfile

DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DAYS_SHORT_FR = ["LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"]
DAYS_SHORT_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

MONTHS_FR = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
MONTHS_EN = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "no_classes_day": "Aucun cours prévu pour cette journée.",
        "no_classes_week": "Aucun cours prévu cette semaine.",
        "schedule_day_title": "📅 Emploi du temps — {date}",
        "schedule_week_title": "📆 Emploi du temps — Semaine {week}",
        "week_of": "Semaine du {start} au {end}",
        "now_title": "⏱️ Cours EPSI — En direct",
        "now_current_class": "🟢 Cours en cours",
        "now_no_current_class": "🟢 Cours en cours : Aucun cours en ce moment.",
        "now_upcoming_classes": "⏳ Prochains cours",
        "now_no_upcoming": "Aucun autre cours prévu prochainement.",
        "teams_link_text": "[Rejoindre la réunion Teams]({url})",
        "room": "Salle",
        "teacher": "Intervenant",
        "time": "Horaires",
        "footer_epsi": "EPSI Bot • Hyperplanning iCal",
        "btn_prev_day": "Jour précédent",
        "btn_next_day": "Jour suivant",
        "btn_prev_week": "Semaine précédente",
        "btn_next_week": "Semaine suivante",
        "btn_refresh": "Actualiser",
        "btn_show_image": "Afficher Image",
        "btn_show_embed": "Afficher Texte",
        "settings_title": "⚙️ Paramètres de votre compte EPSI Bot",
        "settings_not_configured": "Vous n'avez pas encore configuré votre emploi du temps.\n\n👉 Utilisez `/settings register <votre_lien_ical>` pour lier votre Hyperplanning !",
        "settings_ical_field": "🔗 Lien iCal enregistré",
        "settings_daily_field": "⏰ Rappel quotidien (06:00)",
        "settings_weekly_field": "📆 Rappel hebdo (Lundi 06:00)",
        "settings_format_field": "🎨 Format d'affichage",
        "settings_language_field": "🌍 Langue du bot",
        "settings_language_val_fr": "🇫🇷 Français",
        "settings_language_val_en": "🇬🇧 English",
        "settings_enabled": "🟢 Activé",
        "settings_disabled": "🔴 Désactivé",
        "settings_format_img": "🖼️ Image",
        "settings_format_txt": "📄 Embed texte",
        "settings_deleted": "🗑️ Vos informations et votre lien iCal ont été supprimés avec succès.",
        "settings_not_found": "ℹ️ Vous n'étiez pas enregistré dans la base de données.",
        "settings_invalid_url": "❌ **Lien iCal invalide.** L'adresse doit commencer par `http://` ou `https://`.",
        "settings_invalid_ical": "⚠️ Le lien fourni ne semble pas être un fichier calendrier iCal valide (pas de balise VCALENDAR).",
        "settings_access_error": "❌ Impossible d'accéder au lien iCal spécifié : {error}",
        "settings_url_saved": "✅ **Lien iCal Hyperplanning enregistré avec succès !**",
        "settings_must_register": "❌ Veuillez d'abord enregistrer votre lien iCal avec `/settings register:` avant de modifier vos préférences.",
        "settings_daily_updated": "⏰ Rappel quotidien : **{status}**",
        "settings_weekly_updated": "📆 Rappel hebdomadaire : **{status}**",
        "settings_format_updated": "🎨 Format d'affichage par défaut : **{format}**",
        "settings_lang_updated": "🌍 Langue du bot : **{language}**",
        "cron_daily_title": "🌅 Bonjour ! Voici votre emploi du temps du jour :",
        "cron_weekly_title": "🗓️ Bonne semaine ! Voici votre planning hebdomadaire :",
        "image_no_classes": "Aucun cours prévu",
        "image_holiday": "Vacances / Pas de cours",
        "status_activated": "activé",
        "status_deactivated": "désactivé",
    },
    "en": {
        "no_classes_day": "No classes scheduled for this day.",
        "no_classes_week": "No classes scheduled this week.",
        "schedule_day_title": "📅 Schedule — {date}",
        "schedule_week_title": "📆 Schedule — Week {week}",
        "week_of": "Week of {start} to {end}",
        "now_title": "⏱️ EPSI Classes — Live",
        "now_current_class": "🟢 Current Class",
        "now_no_current_class": "🟢 Current Class: No class in progress right now.",
        "now_upcoming_classes": "⏳ Upcoming Classes",
        "now_no_upcoming": "No further classes scheduled soon.",
        "teams_link_text": "[Join Teams meeting]({url})",
        "room": "Room",
        "teacher": "Teacher",
        "time": "Time",
        "footer_epsi": "EPSI Bot • Hyperplanning iCal",
        "btn_prev_day": "Previous Day",
        "btn_next_day": "Next Day",
        "btn_prev_week": "Previous Week",
        "btn_next_week": "Next Week",
        "btn_refresh": "Refresh",
        "btn_show_image": "Show Image",
        "btn_show_embed": "Show Text",
        "settings_title": "⚙️ EPSI Bot Account Settings",
        "settings_not_configured": "You haven't configured your schedule yet.\n\n👉 Use `/settings register <your_ical_url>` to link your Hyperplanning!",
        "settings_ical_field": "🔗 Registered iCal Link",
        "settings_daily_field": "⏰ Daily reminder (06:00)",
        "settings_weekly_field": "📆 Weekly reminder (Mon 06:00)",
        "settings_format_field": "🎨 Display format",
        "settings_language_field": "🌍 Bot Language",
        "settings_language_val_fr": "🇫🇷 Français",
        "settings_language_val_en": "🇬🇧 English",
        "settings_enabled": "🟢 Enabled",
        "settings_disabled": "🔴 Disabled",
        "settings_format_img": "🖼️ Image",
        "settings_format_txt": "📄 Text Embed",
        "settings_deleted": "🗑️ Your account and iCal link have been deleted successfully.",
        "settings_not_found": "ℹ️ You were not registered in the database.",
        "settings_invalid_url": "❌ **Invalid iCal link.** URL must start with `http://` or `https://`.",
        "settings_invalid_ical": "⚠️ The provided link does not appear to be a valid iCal calendar file.",
        "settings_access_error": "❌ Unable to access the specified iCal URL: {error}",
        "settings_url_saved": "✅ **Hyperplanning iCal link registered successfully!**",
        "settings_must_register": "❌ Please register your iCal link with `/settings register:` first before configuring preferences.",
        "settings_daily_updated": "⏰ Daily reminder: **{status}**",
        "settings_weekly_updated": "📆 Weekly reminder: **{status}**",
        "settings_format_updated": "🎨 Default display format: **{format}**",
        "settings_lang_updated": "🌍 Bot language: **{language}**",
        "cron_daily_title": "🌅 Good morning! Here is your schedule for today:",
        "cron_weekly_title": "🗓️ Have a great week! Here is your weekly schedule:",
        "image_no_classes": "No classes scheduled",
        "image_holiday": "Vacation / No classes",
        "status_activated": "enabled",
        "status_deactivated": "disabled",
    },
}


def t(key: str, lang: str = "fr", **kwargs: Any) -> str:
    """Retrieve translated string with optional formatting."""
    lang_dict = TRANSLATIONS.get(lang) or TRANSLATIONS["fr"]
    text = lang_dict.get(key) or TRANSLATIONS["fr"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def format_date_localized(d: date, lang: str = "fr") -> str:
    """Format date into localized string: e.g. 'Lundi 12 octobre 2026' or 'Monday, October 12, 2026'."""
    weekday_idx = d.weekday()
    month_idx = d.month - 1

    if lang == "en":
        day_name = DAYS_EN[weekday_idx]
        month_name = MONTHS_EN[month_idx]
        return f"{day_name}, {month_name} {d.day}, {d.year}"
    else:
        day_name = DAYS_FR[weekday_idx]
        month_name = MONTHS_FR[month_idx]
        return f"{day_name} {d.day} {month_name} {d.year}"


def get_short_day_names(lang: str = "fr") -> list[str]:
    """Return 7 short weekday names (Monday to Sunday)."""
    return DAYS_SHORT_EN if lang == "en" else DAYS_SHORT_FR


def resolve_user_language(
    interaction: discord.Interaction | None = None,
    profile: UserProfile | None = None,
) -> str:
    """Resolve language preference for a user.

    Uses stored profile setting if available, otherwise falls back to
    Discord client locale (if English, returns 'en'), otherwise defaults to 'fr'.
    """
    if profile and profile.language:
        return profile.language.lower()

    if interaction is not None:
        loc = str(interaction.locale).lower()
        if loc.startswith("en"):
            return "en"

    return "fr"
