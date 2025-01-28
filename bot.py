import discord
from discord.ext import commands
import os
import importlib
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Load environment variables
load_dotenv()
google_tokens = [
    os.getenv('GOOGLE_TOKEN_1'),
    os.getenv('GOOGLE_TOKEN_2'),
    os.getenv('GOOGLE_TOKEN_3'),
]
cse_id = os.getenv('GOOGLE_CSE_ID')
lastfm_api_key = os.getenv('LASTFM_API_KEY')

# Import and setup events
import events
events.setup(bot, google_tokens, cse_id, lastfm_api_key)

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


# Run the bot with your token
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
