import asyncio
import logging
import os

import discord
from core.config import *
from core.events import init_events
from database import Album, AlbumIndex, Rating, UserInfo, db
from discord.ext import commands

discord_bot_token = os.getenv("DISCORD_SONATA_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


class SonataBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(command_prefix="!", *args, **kwargs)

        init_events(self)


# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = SonataBot(intents=intents)

initial_extensions = [
    "cogs.artists",
    "cogs.releases",
    "cogs.tracks",
    "cogs.users",
]


async def main() -> None:
    async with bot:
        # Load extensions
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)

            except Exception as e:
                logging.error(f"Failed to load extension {extension}.")
                logging.error(f"Error: {e}")

        # Create the database tables
        with db:
            db.create_tables([Album, AlbumIndex, Rating, UserInfo])

        # Setup logging
        discord.utils.setup_logging()

        if discord_bot_token is None:
            raise ValueError("DISCORD_SONATA_TOKEN environment variable is not set.")

        await bot.start(discord_bot_token)


if __name__ == "__main__":
    asyncio.run(main())
