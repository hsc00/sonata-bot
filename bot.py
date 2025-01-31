import discord
from discord.ext import commands
import os
import importlib
import logging
import events
import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Import and setup events
events.setup(bot, config.google_tokens, config.cse_id, config.cse_id_streaming, config.lastfm_api_key, config.setlist_api_key)

# Load commands
def load_commands():
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            module = importlib.import_module(f'commands.{module_name}')
            if hasattr(module, 'setup'):
                module.setup(bot)
            else:
                print(f"Module {module_name} does not have a setup function.")

load_commands()
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
