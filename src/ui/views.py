"""Interactive Discord UI views with pagination and toggle buttons."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

import discord

from models import CourseEvent
from services.embed_builder import create_day_embed, create_week_embed
from services.ical_service import get_day_schedule, get_week_schedule, strip_teams_links
from services.image_renderer import render_day_image, render_week_image
from services.schedule_enricher import enrich_schedule


class DayScheduleView(discord.ui.View):
    """Interactive view for day schedule with Prev/Next day buttons and Image/Embed toggle."""

    def __init__(
        self,
        ical_url: str,
        current_date: date,
        show_image: bool = True,
        user_id: int | None = None,
        lang: str = "fr",
        show_work_days: bool = True,
        target_tz: str = "Europe/Paris",
        hide_teams: bool = False,
        courses: Sequence[CourseEvent] | None = None,
    ):
        super().__init__(timeout=180)
        self.ical_url = ical_url
        self.current_date = current_date
        self.show_image = show_image
        self.user_id = user_id
        self.lang = lang
        self.show_work_days = show_work_days
        self.target_tz = target_tz
        self.hide_teams = hide_teams
        self.teams_button: discord.ui.Button | None = None

        # Update button labels according to language
        self.prev_day.label = "◀ " + ("Previous Day" if lang == "en" else "Jour précédent")
        self.today.label = "Today" if lang == "en" else "Aujourd'hui"
        self.next_day.label = ("Next Day" if lang == "en" else "Jour suivant") + " ▶"
        self.toggle_view.label = "🖼️ / 📄 " + ("Toggle View" if lang == "en" else "Basculer vue")

        if courses:
            self._sync_teams_button(courses)

    def _sync_teams_button(self, courses: Sequence[CourseEvent]) -> None:
        """Add or update link button to Microsoft Teams if any course has a link."""
        if self.teams_button is not None and self.teams_button in self.children:
            self.remove_item(self.teams_button)
            self.teams_button = None

        if self.hide_teams:
            return

        first_link = next((c.teams_link for c in courses if c.teams_link), None)
        if first_link:
            btn_label = "Join Teams" if self.lang == "en" else "Rejoindre Teams"
            self.teams_button = discord.ui.Button(
                label=btn_label,
                url=first_link,
                style=discord.ButtonStyle.link,
                emoji="🔗",
                row=1,
            )
            self.add_item(self.teams_button)

    async def _update_message(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        raw_courses = await get_day_schedule(self.ical_url, self.current_date)
        courses = await enrich_schedule(
            raw_courses,
            self.current_date,
            self.current_date,
            show_work_days=self.show_work_days,
            lang=self.lang,
        )
        if self.hide_teams:
            courses = strip_teams_links(courses)

        self._sync_teams_button(courses)

        if self.show_image:
            img_buf = render_day_image(
                self.current_date, courses, lang=self.lang, target_tz=self.target_tz
            )
            file = discord.File(img_buf, filename=f"schedule_{self.current_date.isoformat()}.png")
            await interaction.edit_original_response(attachments=[file], embed=None, view=self)
        else:
            embed = create_day_embed(self.current_date, courses, lang=self.lang)
            await interaction.edit_original_response(attachments=[], embed=embed, view=self)

    @discord.ui.button(label="◀ Jour précédent", style=discord.ButtonStyle.secondary)
    async def prev_day(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_date -= timedelta(days=1)
        if self.current_date.weekday() == 6:
            self.current_date -= timedelta(days=2)
        await self._update_message(interaction)

    @discord.ui.button(label="Aujourd'hui", style=discord.ButtonStyle.primary)
    async def today(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_date = date.today()
        await self._update_message(interaction)

    @discord.ui.button(label="Jour suivant ▶", style=discord.ButtonStyle.secondary)
    async def next_day(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_date += timedelta(days=1)
        if self.current_date.weekday() == 5:
            self.current_date += timedelta(days=2)
        await self._update_message(interaction)

    @discord.ui.button(label="🖼️ / 📄 Basculer vue", style=discord.ButtonStyle.success)
    async def toggle_view(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.show_image = not self.show_image
        await self._update_message(interaction)


class WeekScheduleView(discord.ui.View):
    """Interactive view for week schedule with Prev/Next week buttons and Image/Embed toggle."""

    def __init__(
        self,
        ical_url: str,
        start_of_week: date,
        show_image: bool = True,
        user_id: int | None = None,
        lang: str = "fr",
        show_work_days: bool = True,
        target_tz: str = "Europe/Paris",
        hide_teams: bool = False,
        courses: Sequence[CourseEvent] | None = None,
    ):
        super().__init__(timeout=180)
        self.ical_url = ical_url
        self.start_of_week = start_of_week
        self.show_image = show_image
        self.user_id = user_id
        self.lang = lang
        self.show_work_days = show_work_days
        self.target_tz = target_tz
        self.hide_teams = hide_teams
        self.teams_button: discord.ui.Button | None = None

        # Update button labels according to language
        self.prev_week.label = "◀ " + ("Previous Week" if lang == "en" else "Semaine précédente")
        self.current_week.label = "This Week" if lang == "en" else "Cette semaine"
        self.next_week.label = ("Next Week" if lang == "en" else "Semaine suivante") + " ▶"
        self.toggle_view.label = "🖼️ / 📄 " + ("Toggle View" if lang == "en" else "Basculer vue")

        if courses:
            self._sync_teams_button(courses)

    def _sync_teams_button(self, courses: Sequence[CourseEvent]) -> None:
        """Add or update link button to Microsoft Teams if any course has a link."""
        if self.teams_button is not None and self.teams_button in self.children:
            self.remove_item(self.teams_button)
            self.teams_button = None

        if self.hide_teams:
            return

        first_link = next((c.teams_link for c in courses if c.teams_link), None)
        if first_link:
            btn_label = "Join Teams" if self.lang == "en" else "Rejoindre Teams"
            self.teams_button = discord.ui.Button(
                label=btn_label,
                url=first_link,
                style=discord.ButtonStyle.link,
                emoji="🔗",
                row=1,
            )
            self.add_item(self.teams_button)

    async def _update_message(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        raw_courses = await get_week_schedule(self.ical_url, self.start_of_week)
        end_of_week = self.start_of_week + timedelta(days=6)
        courses = await enrich_schedule(
            raw_courses,
            self.start_of_week,
            end_of_week,
            show_work_days=self.show_work_days,
            lang=self.lang,
        )
        if self.hide_teams:
            courses = strip_teams_links(courses)

        self._sync_teams_button(courses)

        if self.show_image:
            img_buf = render_week_image(
                self.start_of_week, courses, lang=self.lang, target_tz=self.target_tz
            )
            file = discord.File(img_buf, filename=f"week_{self.start_of_week.isoformat()}.png")
            await interaction.edit_original_response(attachments=[file], embed=None, view=self)
        else:
            embed = create_week_embed(self.start_of_week, courses, lang=self.lang)
            await interaction.edit_original_response(attachments=[], embed=embed, view=self)

    @discord.ui.button(label="◀ Semaine précédente", style=discord.ButtonStyle.secondary)
    async def prev_week(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.start_of_week -= timedelta(days=7)
        await self._update_message(interaction)

    @discord.ui.button(label="Cette semaine", style=discord.ButtonStyle.primary)
    async def current_week(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        today = date.today()
        self.start_of_week = today - timedelta(days=today.weekday())
        await self._update_message(interaction)

    @discord.ui.button(label="Semaine suivante ▶", style=discord.ButtonStyle.secondary)
    async def next_week(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.start_of_week += timedelta(days=7)
        await self._update_message(interaction)

    @discord.ui.button(label="🖼️ / 📄 Basculer vue", style=discord.ButtonStyle.success)
    async def toggle_view(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.show_image = not self.show_image
        await self._update_message(interaction)
