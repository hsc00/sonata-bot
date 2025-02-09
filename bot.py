import discord
from discord.ext import commands
import os
import importlib
import events
from config import *
import ratings_cache

# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Import and setup events
events.setup(bot)

# Load commands
def load_commands():
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            module_name = f'commands.{filename[:-3]}'
            module = importlib.import_module(module_name)
            
            if hasattr(module, 'setup'):
                module.setup(bot)
            else:
                print(f"Module {module_name} does not have a setup function.")

load_commands()
ratings_cache.load()
################# Choose the production bot token ###################
discord_bot_token = os.getenv('DISCORD_SONATA_TOKEN')
#####################################################################
async def on_ready():
    print(f'Logged in as {bot.user}')
    if discord_bot_token[-1] == 'E':
        channel = bot.get_channel(1039885578155597854)
        await channel.send('I am back online!')

bot.add_listener(on_ready)
bot.run(discord_bot_token)
