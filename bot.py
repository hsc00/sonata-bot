import discord
from discord.ext import commands
import asyncio
import os
import importlib
import events
from config import *
from discord.ext.commands import Context
from commands.randomrating import get_random_rating
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
        channel = bot.get_channel(1039885578155597854)
        await channel.send('I am back online!')
        asyncio.create_task(periodic_tasks(channel))

class BotMessage:
    def __init__(self, channel, author, content):
        self.channel = channel
        self.author = author
        self.content = content
        self.guild = channel.guild
        self._state = channel._state
        self.id = 1

async def periodic_tasks(channel):
    while True:
        await asyncio.sleep(21600) # Sends a random rating every 6 hours
        author = bot.user
        bot_message = BotMessage(channel, author, '!randomrating')
        
        ctx = await bot.get_context(bot_message, cls=commands.Context)
        async with ctx.channel.typing():
            await get_random_rating(ctx)

bot.add_listener(on_ready)
bot.run(discord_bot_token)
