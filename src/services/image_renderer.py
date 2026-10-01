"""Schedule image generator using Pillow (pure Python, crisp Discord dark aesthetics)."""

from __future__ import annotations

import colorsys
import io
import os
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from models import CourseEvent
from services.i18n import DAYS_EN, DAYS_FR, MONTHS_EN, MONTHS_FR, t
from services.ical_service import convert_course_timezone

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

COLOR_BG = (17, 24, 39)  # Dark slate #111827
COLOR_GRID_BG = (24, 32, 47)  # Day column background
COLOR_CARD_BORDER = (55, 65, 81)  # Grid & card border #374151
COLOR_GRID_LINE = (38, 48, 66)  # Subtle hour dividers
COLOR_TEXT_MAIN = (243, 244, 246)  # White/light #F3F4F6
COLOR_TEXT_MUTED = (156, 163, 175)  # Gray #9CA3AF
COLOR_ACCENT = (59, 130, 246)  # EPSI / Discord Blue #3B82F6


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font supporting accented French Unicode characters."""
    font_names = (
        ["Roboto-Bold.ttf", "segoeuib.ttf", "arialbd.ttf"]
        if bold
        else ["Roboto-Regular.ttf", "segoeui.ttf", "arial.ttf"]
    )

    # 1. Try bundled font-roboto package
    try:
        import font_roboto

        roboto_file = getattr(font_roboto, "Roboto", None)
        if roboto_file:
            font_dir = Path(os.path.dirname(roboto_file))
            chosen_roboto = "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"
            font_path = font_dir / chosen_roboto
            if font_path.exists():
                return ImageFont.truetype(str(font_path), size)
    except Exception:
        pass

    # 2. Try common system fonts on Windows / Linux
    search_dirs = [
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype"),
    ]

    for d in search_dirs:
        for fname in font_names:
            candidate = d / fname
            if candidate.exists():
                try:
                    return ImageFont.truetype(str(candidate), size)
                except Exception:
                    continue

    # Fallback to Pillow default
    return ImageFont.load_default(size=size)


def get_course_colors(
    course_name: str, event_type: str = "course"
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Generate consistent (card_background, accent_badge) colors for a course.

    Matches Hyperplanning pastel card style with soft tint and vibrant accent.
    """
    if event_type == "holiday":
        # Warm amber / gold
        return (60, 40, 15), (245, 158, 11)
    if event_type == "work":
        # Professional teal / cyan
        return (15, 55, 60), (20, 184, 166)

    seed_val = sum(ord(c) for c in course_name)
    hue = (seed_val % 360) / 360.0

    # Vibrant accent
    ar, ag, ab = colorsys.hsv_to_rgb(hue, 0.75, 0.90)
    accent = (int(ar * 255), int(ag * 255), int(ab * 255))

    # Muted dark-pastel background
    br, bg, bb = colorsys.hsv_to_rgb(hue, 0.35, 0.26)
    card_bg = (int(br * 255), int(bg * 255), int(bb * 255))

    return card_bg, accent


def render_day_image(
    target_date: date,
    courses: Sequence[CourseEvent],
    lang: str = "fr",
    target_tz: str = "Europe/Paris",
) -> io.BytesIO:
    """Render a clean, high-resolution daily schedule card with Pillow."""
    if target_tz and target_tz != "Europe/Paris":
        courses = [convert_course_timezone(c, target_tz) for c in courses]

    width = 850
    card_margin = 30
    card_spacing = 16
    header_height = 100
    card_height = 110

    total_courses = len(courses)
    if total_courses == 0:
        height = header_height + 150
    else:
        height = header_height + total_courses * (card_height + card_spacing) + 40

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_large = get_font(24, bold=True)
    font_medium = get_font(18, bold=True)
    font_small = get_font(14)

    # Header section
    weekday_str = (DAYS_EN if lang == "en" else DAYS_FR)[target_date.weekday()]
    month_str = (MONTHS_EN if lang == "en" else MONTHS_FR)[target_date.month - 1]
    title_text = (
        f"{weekday_str}, {month_str} {target_date.day}, {target_date.year}"
        if lang == "en"
        else f"{weekday_str} {target_date.day} {month_str} {target_date.year}"
    )

    # Header top bar accent
    draw.rectangle([0, 0, width, 6], fill=COLOR_ACCENT)
    draw.text((card_margin, 35), title_text, fill=COLOR_TEXT_MAIN, font=font_large)

    courses_label = "classes" if lang == "en" else "cours"
    subtitle_prefix = "EPSI Timetable" if lang == "en" else "Emploi du temps EPSI"
    tz_suffix = f" • {target_tz}" if (target_tz and target_tz != "Europe/Paris") else ""
    subtitle_text = f"{subtitle_prefix} • {total_courses} {courses_label}{tz_suffix}"
    draw.text((card_margin, 68), subtitle_text, fill=COLOR_TEXT_MUTED, font=font_small)

    if total_courses == 0:
        box_top = header_height + 20
        box_rect = [card_margin, box_top, width - card_margin, box_top + 80]
        draw.rounded_rectangle(box_rect, radius=12, fill=(31, 41, 55), outline=COLOR_CARD_BORDER)
        draw.text(
            (card_margin + 30, box_top + 30),
            f"🎉 {t('no_classes_day', lang=lang)}",
            fill=COLOR_TEXT_MAIN,
            font=font_medium,
        )
    else:
        curr_y = header_height + 15
        for course in courses:
            card_rect = [card_margin, curr_y, width - card_margin, curr_y + card_height]
            card_bg, accent = get_course_colors(course.name, course.event_type)
            draw.rounded_rectangle(card_rect, radius=12, fill=card_bg, outline=COLOR_CARD_BORDER)

            # Left accent badge
            draw.rounded_rectangle(
                [card_margin, curr_y, card_margin + 8, curr_y + card_height],
                radius=4,
                fill=accent,
            )

            # Time column
            time_str = course.time_range_str
            draw.text(
                (card_margin + 25, curr_y + 20), time_str, fill=COLOR_ACCENT, font=font_medium
            )
            dur_str = f"({course.duration_minutes} min)"
            draw.text(
                (card_margin + 25, curr_y + 48), dur_str, fill=COLOR_TEXT_MUTED, font=font_small
            )

            # Course details column
            details_x = card_margin + 175
            course_name = course.name
            if len(course_name) > 45:
                course_name = course_name[:42] + "..."
            draw.text((details_x, curr_y + 20), course_name, fill=COLOR_TEXT_MAIN, font=font_medium)

            # Room & Teacher line
            meta_parts = []
            if course.room:
                meta_parts.append(f"Salle: {course.room}")
            if course.teacher:
                meta_parts.append(f"Prof: {course.teacher}")
            if course.teams_link:
                meta_parts.append("Visio Teams")

            meta_str = (
                "  •  ".join(meta_parts) if meta_parts else "Aucune information supplémentaire"
            )
            if len(meta_str) > 65:
                meta_str = meta_str[:62] + "..."
            draw.text((details_x, curr_y + 55), meta_str, fill=COLOR_TEXT_MUTED, font=font_small)

            curr_y += card_height + card_spacing

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def render_week_image(
    start_of_week: date,
    courses: Sequence[CourseEvent],
    lang: str = "fr",
    target_tz: str = "Europe/Paris",
) -> io.BytesIO:
    """Render a weekly calendar timetable with proportional time slots (08:00 - 19:00).

    Classes span proportionally across their hours (e.g. 9-13 expands across 4 slots),
    just like the official Hyperplanning portal grid.
    """
    if target_tz and target_tz != "Europe/Paris":
        courses = [convert_course_timezone(c, target_tz) for c in courses]

    days_to_show = 5  # Mon to Fri
    start_hour = 8  # Default 08:00
    end_hour = 19  # Default 19:00

    non_all_day = [c for c in courses if c.event_type != "holiday"]
    if non_all_day:
        earliest_start = min(c.start.hour for c in non_all_day)
        latest_end = max(c.end.hour + (1 if c.end.minute > 0 else 0) for c in non_all_day)

        # If timezone shifted earlier (e.g. US timezones: 02:00 to 11:00)
        if earliest_start < 8:
            start_hour = max(0, earliest_start)
            end_hour = min(24, max(start_hour + 8, latest_end + 1))
        # If timezone shifted later (e.g. Asia timezones: 15:00 to 23:00)
        elif earliest_start >= 12:
            start_hour = max(0, earliest_start - 1)
            end_hour = min(24, max(start_hour + 8, latest_end + 1))
        else:
            # Standard daytime: keep 8 to 19, or expand if earlier/later classes exist
            start_hour = min(start_hour, earliest_start)
            end_hour = max(end_hour, latest_end)

    start_hour = max(0, min(start_hour, 23))
    end_hour = max(start_hour + 1, min(end_hour, 24))
    total_hours = end_hour - start_hour

    hour_height = 68  # Pixels per 1-hour slot
    time_col_width = 70  # Left axis for 08:00, 09:00, etc.
    day_width = 245
    gap = 8
    margin_x = 24
    margin_y = 20
    header_h = 75
    day_header_h = 42

    grid_h = total_hours * hour_height
    grid_top = margin_y + header_h + day_header_h

    total_width = (
        margin_x * 2 + time_col_width + days_to_show * day_width + (days_to_show - 1) * gap
    )
    total_height = grid_top + grid_h + 25

    img = Image.new("RGB", (total_width, total_height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_title = get_font(24, bold=True)
    font_day = get_font(15, bold=True)
    font_hour = get_font(12, bold=True)
    font_course_name = get_font(13, bold=True)
    font_course_meta = get_font(11)
    font_course_time = get_font(11, bold=True)

    # Top accent bar
    draw.rectangle([0, 0, total_width, 6], fill=COLOR_ACCENT)

    # Header title
    week_num = start_of_week.isocalendar()[1]
    title = (
        f"EPSI Schedule • Week {week_num}"
        if lang == "en"
        else f"Emploi du temps EPSI • Semaine {week_num}"
    )
    draw.text((margin_x, margin_y + 10), title, fill=COLOR_TEXT_MAIN, font=font_title)

    month_name = (MONTHS_EN if lang == "en" else MONTHS_FR)[start_of_week.month - 1]
    tz_suffix = f" • {target_tz}" if (target_tz and target_tz != "Europe/Paris") else ""
    range_str = (
        f"Week of {start_of_week.day} to {start_of_week.day + 4} {month_name} {start_of_week.year}{tz_suffix}"
        if lang == "en"
        else f"Du {start_of_week.day} au {start_of_week.day + 4} {month_name} {start_of_week.year}{tz_suffix}"
    )
    draw.text((margin_x, margin_y + 44), range_str, fill=COLOR_TEXT_MUTED, font=font_course_meta)

    # Left Time Axis (Hours labels 08:00 to 19:00)
    for h in range(start_hour, end_hour + 1):
        y_pos = grid_top + (h - start_hour) * hour_height
        hour_label = f"{h:02d}:00" if lang == "en" else f"{h:02d}h00"
        draw.text(
            (margin_x + 6, y_pos - 8),
            hour_label,
            fill=COLOR_TEXT_MUTED,
            font=font_hour,
        )

    # Group courses by day offset (0: Monday, 4: Friday)
    courses_by_day: dict[int, list[CourseEvent]] = {i: [] for i in range(days_to_show)}
    for course in courses:
        day_diff = (course.event_date - start_of_week).days
        if 0 <= day_diff < days_to_show:
            courses_by_day[day_diff].append(course)

    # Render day columns and grid
    for i in range(days_to_show):
        col_x = margin_x + time_col_width + i * (day_width + gap)

        # 1. Day Column Header
        header_rect = [col_x, margin_y + header_h, col_x + day_width, grid_top - 4]
        draw.rounded_rectangle(header_rect, radius=6, fill=(31, 41, 55), outline=COLOR_CARD_BORDER)
        cur_day = start_of_week.day + i
        day_name = (DAYS_EN if lang == "en" else DAYS_FR)[i]
        day_title = f"{day_name} {cur_day}"
        draw.text(
            (col_x + 14, margin_y + header_h + 12),
            day_title,
            fill=COLOR_TEXT_MAIN,
            font=font_day,
        )

        # 2. Day Background Grid Column
        body_rect = [col_x, grid_top, col_x + day_width, grid_top + grid_h]
        draw.rounded_rectangle(body_rect, radius=6, fill=COLOR_GRID_BG, outline=COLOR_CARD_BORDER)

        # Horizontal subtle hour dividing lines
        for h in range(start_hour + 1, end_hour):
            y_line = grid_top + (h - start_hour) * hour_height
            draw.line([(col_x + 1, y_line), (col_x + day_width - 2, y_line)], fill=COLOR_GRID_LINE)

        # 3. Render proportional course cards on the time scale
        day_courses = sorted(courses_by_day[i], key=lambda c: c.start)
        for course in day_courses:
            # Start and End in decimal hours (e.g. 09:30 -> 9.5)
            start_decimal = course.start.hour + course.start.minute / 60.0
            end_decimal = course.end.hour + course.end.minute / 60.0

            # Clamp to grid bounds
            clamped_start = max(start_decimal, float(start_hour))
            clamped_end = min(end_decimal, float(end_hour))

            if clamped_end <= clamped_start:
                continue

            card_y1 = grid_top + int((clamped_start - start_hour) * hour_height) + 2
            card_y2 = grid_top + int((clamped_end - start_hour) * hour_height) - 2
            card_h = card_y2 - card_y1

            card_bg, accent = get_course_colors(course.name, course.event_type)
            card_rect = [col_x + 4, card_y1, col_x + day_width - 4, card_y2]

            # Render card background with rounded corners and border
            draw.rounded_rectangle(card_rect, radius=6, fill=card_bg, outline=accent, width=1)

            # Left color badge line
            draw.rounded_rectangle(
                [col_x + 4, card_y1, col_x + 9, card_y2],
                radius=2,
                fill=accent,
            )

            # Content inside proportional block
            text_x = col_x + 15
            curr_text_y = card_y1 + 6

            # Time header inside card
            draw.text(
                (text_x, curr_text_y),
                course.time_range_str,
                fill=accent,
                font=font_course_time,
            )
            curr_text_y += 18

            # Course Name (word-wrapped if block is tall enough)
            words = course.name.split()
            lines: list[str] = []
            cur_line = ""
            for word in words:
                test_line = f"{cur_line} {word}".strip()
                if len(test_line) <= 24:
                    cur_line = test_line
                else:
                    lines.append(cur_line)
                    cur_line = word
            if cur_line:
                lines.append(cur_line)

            max_lines = 3 if card_h > 110 else (2 if card_h > 70 else 1)
            for line_idx, line_text in enumerate(lines[:max_lines]):
                if line_idx == max_lines - 1 and len(lines) > max_lines:
                    line_text = line_text[:20] + "..."
                draw.text(
                    (text_x, curr_text_y), line_text, fill=COLOR_TEXT_MAIN, font=font_course_name
                )
                curr_text_y += 16

            # Teacher (only if sufficient vertical space)
            if card_h >= 75 and course.teacher:
                teacher_prefix = "Teacher" if lang == "en" else "Prof"
                teacher_text = f"{teacher_prefix}: {course.teacher}"
                if len(teacher_text) > 26:
                    teacher_text = teacher_text[:24] + "..."
                draw.text(
                    (text_x, curr_text_y + 3),
                    teacher_text,
                    fill=COLOR_TEXT_MUTED,
                    font=font_course_meta,
                )
                curr_text_y += 15

            # Room (if space allows)
            if card_h >= 95 and course.room:
                room_prefix = "Room" if lang == "en" else "Salle"
                room_text = f"{room_prefix}: {course.room}"
                if len(room_text) > 26:
                    room_text = room_text[:24] + "..."
                draw.text(
                    (text_x, curr_text_y + 2),
                    room_text,
                    fill=COLOR_TEXT_MUTED,
                    font=font_course_meta,
                )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
