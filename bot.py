import discord
from discord.ext import commands
import asyncio
import os
import importlib
import events
from config import *
from cronjobs import *
import API.ratings_cache as ratings_cache

# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the intent to read message content

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.errors.CommandNotFound):
        pass  # Suppress the warning for CommandNotFound
    else:
        raise error
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        pass  # Suppress the warning for CommandNotFound
    else:
        raise error
    
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
        music_channel = bot.get_channel(1039885578155597854)
        new_releases_channel = bot.get_channel(1245325666900115517)
        await music_channel.send('I am back online! Hopefully Skelozard fed me some new updates 👀')
        asyncio.create_task(periodic_tasks(music_channel, new_releases_channel))

class BotMessage:
    def __init__(self, channel, author, content):
        self.channel = channel
        self.author = author
        self.content = content
        self.guild = channel.guild
        self._state = channel._state
        self.id = 1

async def periodic_tasks(music_channel, new_releases_channel):
    while True:
        random_rating_task = asyncio.create_task(random_rating_cronjob(music_channel, bot, BotMessage))
        new_releases_task = asyncio.create_task(new_releases_friday(new_releases_channel, bot, BotMessage))
        
        await asyncio.gather(random_rating_task, new_releases_task)

bot.add_listener(on_ready)
bot.run(discord_bot_token)
