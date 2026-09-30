"""Interactive Discord UI views with pagination and toggle buttons."""

from __future__ import annotations

from datetime import date, timedelta

import discord

from services.embed_builder import create_day_embed, create_week_embed
from services.ical_service import get_day_schedule, get_week_schedule
from services.image_renderer import render_day_image, render_week_image


class DayScheduleView(discord.ui.View):
    """Interactive view for day schedule with Prev/Next day buttons and Image/Embed toggle."""

    def __init__(
        self,
        ical_url: str,
        current_date: date,
        show_image: bool = True,
        user_id: int | None = None,
    ):
        super().__init__(timeout=180)
        self.ical_url = ical_url
        self.current_date = current_date
        self.show_image = show_image
        self.user_id = user_id

    async def _update_message(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        courses = await get_day_schedule(self.ical_url, self.current_date)

        if self.show_image:
            img_buf = render_day_image(self.current_date, courses)
            file = discord.File(img_buf, filename=f"schedule_{self.current_date.isoformat()}.png")
            await interaction.edit_original_response(attachments=[file], embed=None, view=self)
        else:
            embed = create_day_embed(self.current_date, courses)
            await interaction.edit_original_response(attachments=[], embed=embed, view=self)

    @discord.ui.button(label="◀ Jour précédent", style=discord.ButtonStyle.secondary)
    async def prev_day(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_date -= timedelta(days=1)
        # Skip weekends if on Sunday moving back
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
        # Skip weekend if on Saturday moving forward
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
    ):
        super().__init__(timeout=180)
        self.ical_url = ical_url
        self.start_of_week = start_of_week
        self.show_image = show_image
        self.user_id = user_id

    async def _update_message(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        courses = await get_week_schedule(self.ical_url, self.start_of_week)

        if self.show_image:
            img_buf = render_week_image(self.start_of_week, courses)
            file = discord.File(img_buf, filename=f"week_{self.start_of_week.isoformat()}.png")
            await interaction.edit_original_response(attachments=[file], embed=None, view=self)
        else:
            embed = create_week_embed(self.start_of_week, courses)
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
