import asyncio
import logging

import discord
from core.config import discord_bot_token
from core.embeds import EmbedBuilder
from core.events import init_events
from database import Album, AlbumIndex, Rating, UserInfo, db
from discord.ext import commands

logger = logging.getLogger(__name__)


class SonataBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        init_events(self)


# Define the intents
intents = discord.Intents.default()
intents.members = True  # Enable the members intent
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = SonataBot(command_prefix="!", intents=intents, help_command=None)

initial_extensions = [
    "cogs.artists",
    "cogs.releases",
    "cogs.tracks",
    "cogs.users",
]


@bot.hybrid_command(name="help", with_app_command=True)
async def help_command(ctx: commands.Context) -> None:
    """Get help and documentation for Sonata Bot."""
    embed = (
        EmbedBuilder()
        .with_title("Help & Documentation")
        .with_description(
            "For detailed documentation, commands, and setup instructions, visit: [Sonata Bot Documentation](https://hsc00.github.io/sonata-bot/)"
        )
        .with_color(discord.Color.blue())
        .build()
    )

    await ctx.send(embed=embed)


async def main() -> None:
    async with bot:
        # Load extensions
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)

            except Exception:
                logger.exception(f"Failed to load extension {extension}.")

        # Create the database tables
        with db:
            db.create_tables([Album, AlbumIndex, Rating, UserInfo])

        # Setup logging
        discord.utils.setup_logging()

        if discord_bot_token is None:
            raise ValueError("DISCORD_SONATA_TOKEN environment variable is not set.")

        await bot.start(discord_bot_token)


asyncio.run(main())
