"""Rich Discord embed generators for day, week, and now schedules."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime

import discord

from models import CourseEvent

FRENCH_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
FRENCH_MONTHS = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


def format_date_fr(d: date) -> str:
    """Format date to French readable string."""
    return f"{FRENCH_DAYS[d.weekday()]} {d.day} {FRENCH_MONTHS[d.month - 1]} {d.year}"


def create_day_embed(target_date: date, courses: Sequence[CourseEvent]) -> discord.Embed:
    """Create a formatted Discord Embed for a single day schedule."""
    embed = discord.Embed(
        title=f"📅 Emploi du temps — {format_date_fr(target_date)}",
        color=discord.Color.from_rgb(59, 130, 246),
        timestamp=datetime.now(UTC),
    )

    if not courses:
        embed.description = (
            "🎉 **Aucun cours prévu pour cette journée !** Profitez de votre temps libre."
        )
        return embed

    embed.description = f"**{len(courses)}** cours au programme :"

    for course in courses:
        fields = [f"⏰ **{course.time_range_str}** ({course.duration_minutes} min)"]
        if course.room:
            fields.append(f"📍 Salle: `{course.room}`")
        if course.teacher:
            fields.append(f"👤 Intervenant: {course.teacher}")
        if course.group:
            fields.append(f"👥 Groupe: {course.group}")
        if course.teams_link:
            fields.append(f"🔗 [Lien Visio Teams]({course.teams_link})")

        embed.add_field(
            name=f"📘 {course.name}",
            value="\n".join(fields),
            inline=False,
        )

    embed.set_footer(text="EPSI Bot • Hyperplanning iCal")
    return embed


def create_week_embed(start_of_week: date, courses: Sequence[CourseEvent]) -> discord.Embed:
    """Create a formatted Discord Embed for a week schedule."""
    week_num = start_of_week.isocalendar()[1]
    desc = f"Semaine du {start_of_week.day} {FRENCH_MONTHS[start_of_week.month - 1]} {start_of_week.year}"
    if not courses:
        desc += "\n\n🎉 Aucun cours de planifié pour toute la semaine !"

    embed = discord.Embed(
        title=f"📆 Emploi du temps — Semaine {week_num}",
        description=desc,
        color=discord.Color.from_rgb(59, 130, 246),
        timestamp=datetime.now(UTC),
    )

    if not courses:
        return embed

    # Group by date
    courses_by_date: dict[date, list[CourseEvent]] = {}
    for course in courses:
        courses_by_date.setdefault(course.event_date, []).append(course)

    for d, day_courses in sorted(courses_by_date.items()):
        day_lines = []
        for c in day_courses:
            meta_items = []
            if c.teacher:
                meta_items.append(c.teacher)
            if c.room:
                meta_items.append(f"`{c.room}`")
            meta_info = f" ({', '.join(meta_items)})" if meta_items else ""
            day_lines.append(f"`{c.time_range_str}` **{c.name}**{meta_info}")

        embed.add_field(
            name=format_date_fr(d),
            value="\n".join(day_lines) if day_lines else "Pas de cours",
            inline=False,
        )

    embed.set_footer(text="EPSI Bot • Hyperplanning iCal")
    return embed


def create_now_embed(
    current_course: CourseEvent | None,
    upcoming_courses: Sequence[CourseEvent],
) -> discord.Embed:
    """Create an embed showing current running course and upcoming courses."""
    embed = discord.Embed(
        title="⏱️ Point cours en direct",
        color=discord.Color.green() if current_course else discord.Color.blue(),
        timestamp=datetime.now(UTC),
    )

    if current_course:
        details = [
            f"⏰ **Horaire :** {current_course.time_range_str}",
            f"📍 **Salle :** `{current_course.room or 'Non spécifiée'}`",
            f"👤 **Intervenant :** {current_course.teacher or 'Non spécifié'}",
        ]
        if current_course.teams_link:
            details.append(f"🔗 [Rejoindre sur Teams]({current_course.teams_link})")

        embed.add_field(
            name=f"🟢 En cours actuellement : {current_course.name}",
            value="\n".join(details),
            inline=False,
        )
    else:
        embed.add_field(
            name="⚪ Aucun cours en cours",
            value="Vous n'avez pas de classe active actuellement.",
            inline=False,
        )

    if upcoming_courses:
        next_lines = []
        for c in upcoming_courses:
            date_prefix = (
                f"{FRENCH_DAYS[c.event_date.weekday()]} "
                if c.event_date != datetime.now().date()
                else ""
            )
            room = f" (`{c.room}`)" if c.room else ""
            next_lines.append(f"• **{date_prefix}{c.time_range_str}** — {c.name}{room}")

        embed.add_field(
            name="🔜 Prochains cours :",
            value="\n".join(next_lines),
            inline=False,
        )

    embed.set_footer(text="EPSI Bot • Hyperplanning iCal")
    return embed
