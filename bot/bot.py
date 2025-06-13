import asyncio
import discord
import events

from discord.ext import commands

from config import *
from database import *

discord_bot_token = os.getenv("DISCORD_SONATA_TOKEN")


class BotMessage:
    def __init__(self, channel, author, content):
        self.channel = channel
        self.author = author
        self.content = content
        self.guild = channel.guild
        self._state = channel._state
        self.id = 1


class SonataBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="!", *args, **kwargs)
        self.initial_extensions = [
            "cogs.album",
        ]


# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = SonataBot(intents=intents)

# Import and setup events
events.setup(bot)

initial_extensions = [
    "cogs.artists",
    "cogs.ratings",
    "cogs.releases",
    "cogs.users"
]


async def main():
    async with bot:
        # Load extensions
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)

            except Exception:
                print(f"Failed to load extension {extension}.")

        # Create the database tables
        with db:
            db.create_tables([Album, AlbumIndex, Rating, UserInfo])

        # Setup logging
        discord.utils.setup_logging()

        await bot.start(discord_bot_token)


asyncio.run(main())
