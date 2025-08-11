import discord


class PaginatorView(discord.ui.View):
    def __init__(self, pages: list, timeout: int = 60) -> None:
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0

    async def update_message(self, interaction: discord.Interaction) -> None:
        embed = self.pages[self.current_page]

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.primary, disabled=False)
    async def first_button(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:

        self.current_page = 0

        if self.current_page == 0:
            self.next_button.disabled = False

        self.previous_button.disabled = True

        await self.update_message(interaction)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.current_page -= 1

        if self.current_page == 0:
            self.previous_button.disabled = True

        self.next_button.disabled = False

        await self.update_message(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.current_page += 1

        if self.current_page == len(self.pages) - 1:
            self.next_button.disabled = True

        self.previous_button.disabled = False

        await self.update_message(interaction)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.primary)
    async def last_button(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.current_page = len(self.pages) - 1

        if self.current_page == len(self.pages) - 1:
            self.next_button.disabled = True

        self.previous_button.disabled = False

        await self.update_message(interaction)
