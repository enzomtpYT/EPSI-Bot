"""Rich Discord embed generators for day, week, and now schedules."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime

import discord

from models import CourseEvent
from services.i18n import (
    DAYS_EN,
    DAYS_FR,
    MONTHS_EN,
    MONTHS_FR,
    format_date_localized,
    t,
)


def create_day_embed(
    target_date: date, courses: Sequence[CourseEvent], lang: str = "fr"
) -> discord.Embed:
    """Create a formatted Discord Embed for a single day schedule."""
    formatted_date = format_date_localized(target_date, lang=lang)
    title = t("schedule_day_title", lang=lang, date=formatted_date)

    embed = discord.Embed(
        title=title,
        color=discord.Color.from_rgb(59, 130, 246),
        timestamp=datetime.now(UTC),
    )

    if not courses:
        embed.description = f"🎉 **{t('no_classes_day', lang=lang)}**"
        embed.set_footer(text=t("footer_epsi", lang=lang))
        return embed

    courses_label = "classes scheduled:" if lang == "en" else "cours au programme :"
    embed.description = f"**{len(courses)}** {courses_label}"

    room_label = t("room", lang=lang)
    teacher_label = t("teacher", lang=lang)

    for course in courses:
        fields = [f"⏰ **{course.time_range_str}** ({course.duration_minutes} min)"]
        if course.room:
            fields.append(f"📍 {room_label}: `{course.room}`")
        if course.teacher:
            fields.append(f"👤 {teacher_label}: {course.teacher}")
        if course.group:
            group_label = "Group" if lang == "en" else "Groupe"
            fields.append(f"👥 {group_label}: {course.group}")
        if course.teams_link:
            teams_text = t("teams_link_text", lang=lang, url=course.teams_link)
            fields.append(f"🔗 {teams_text}")

        if course.event_type == "holiday":
            prefix = "🎉"
        elif course.event_type == "work":
            prefix = "💼"
        else:
            prefix = "📘"

        embed.add_field(
            name=f"{prefix} {course.name}",
            value="\n".join(fields),
            inline=False,
        )

    embed.set_footer(text=t("footer_epsi", lang=lang))
    return embed


def create_week_embed(
    start_of_week: date, courses: Sequence[CourseEvent], lang: str = "fr"
) -> discord.Embed:
    """Create a formatted Discord Embed for a week schedule."""
    week_num = start_of_week.isocalendar()[1]
    title = t("schedule_week_title", lang=lang, week=week_num)

    month_name = (MONTHS_EN if lang == "en" else MONTHS_FR)[start_of_week.month - 1]
    if lang == "en":
        desc = f"Week of {start_of_week.day} to {start_of_week.day + 4} {month_name} {start_of_week.year}"
    else:
        desc = f"Semaine du {start_of_week.day} au {start_of_week.day + 4} {month_name} {start_of_week.year}"

    if not courses:
        desc += f"\n\n🎉 {t('no_classes_week', lang=lang)}"

    embed = discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.from_rgb(59, 130, 246),
        timestamp=datetime.now(UTC),
    )

    if not courses:
        embed.set_footer(text=t("footer_epsi", lang=lang))
        return embed

    # Group by date
    courses_by_date: dict[date, list[CourseEvent]] = {}
    for course in courses:
        courses_by_date.setdefault(course.event_date, []).append(course)

    for d, day_courses in sorted(courses_by_date.items()):
        day_lines = []
        for c in day_courses:
            if c.event_type == "holiday":
                day_lines.append(f"🎉 **{c.name}** ({c.room})")
            elif c.event_type == "work":
                day_lines.append(f"💼 `{c.time_range_str}` **{c.name}** ({c.room})")
            else:
                meta_items = []
                if c.teacher:
                    meta_items.append(c.teacher)
                if c.room:
                    meta_items.append(f"`{c.room}`")
                meta_info = f" ({', '.join(meta_items)})" if meta_items else ""
                day_lines.append(f"`{c.time_range_str}` **{c.name}**{meta_info}")

        embed.add_field(
            name=format_date_localized(d, lang=lang),
            value="\n".join(day_lines) if day_lines else t("no_classes_day", lang=lang),
            inline=False,
        )

    embed.set_footer(text=t("footer_epsi", lang=lang))
    return embed


def create_now_embed(
    current_course: CourseEvent | None,
    upcoming_courses: Sequence[CourseEvent],
    lang: str = "fr",
) -> discord.Embed:
    """Create an embed showing current running course and upcoming courses."""
    color = discord.Color.blue()
    if current_course:
        if current_course.event_type == "holiday":
            color = discord.Color.gold()
        elif current_course.event_type == "work":
            color = discord.Color.teal()
        else:
            color = discord.Color.green()

    embed = discord.Embed(
        title=t("now_title", lang=lang),
        color=color,
        timestamp=datetime.now(UTC),
    )

    room_label = t("room", lang=lang)
    teacher_label = t("teacher", lang=lang)

    if current_course:
        if current_course.event_type == "holiday":
            current_header = f"🎉 {current_course.name}"
            details = [f"📍 **{room_label} :** `{current_course.room}`"]
        elif current_course.event_type == "work":
            current_header = f"💼 {current_course.name}"
            details = [
                f"⏰ **{t('time', lang=lang)} :** {current_course.time_range_str}",
                f"📍 **{room_label} :** `{current_course.room}`",
            ]
        else:
            details = [
                f"⏰ **{t('time', lang=lang)} :** {current_course.time_range_str}",
                f"📍 **{room_label} :** `{current_course.room or ('Not specified' if lang == 'en' else 'Non spécifiée')}`",
                f"👤 **{teacher_label} :** {current_course.teacher or ('Not specified' if lang == 'en' else 'Non spécifié')}",
            ]
            if current_course.teams_link:
                details.append(
                    f"🔗 {t('teams_link_text', lang=lang, url=current_course.teams_link)}"
                )

            current_header = (
                f"🟢 Currently in progress: {current_course.name}"
                if lang == "en"
                else f"🟢 En cours actuellement : {current_course.name}"
            )

        embed.add_field(
            name=current_header,
            value="\n".join(details),
            inline=False,
        )
    else:
        embed.add_field(
            name="⚪ " + ("No class in progress" if lang == "en" else "Aucun cours en cours"),
            value=(
                "You don't have any active class right now."
                if lang == "en"
                else "Vous n'avez pas de classe active actuellement."
            ),
            inline=False,
        )

    if upcoming_courses:
        next_lines = []
        days_names = DAYS_EN if lang == "en" else DAYS_FR
        for c in upcoming_courses:
            date_prefix = (
                f"{days_names[c.event_date.weekday()]} "
                if c.event_date != datetime.now().date()
                else ""
            )
            room = f" (`{c.room}`)" if c.room else ""
            next_lines.append(f"• **{date_prefix}{c.time_range_str}** — {c.name}{room}")

        upcoming_header = t("now_upcoming_classes", lang=lang) + " :"
        embed.add_field(
            name=upcoming_header,
            value="\n".join(next_lines),
            inline=False,
        )

    embed.set_footer(text=t("footer_epsi", lang=lang))
    return embed
