import json
import os
from discord.ext import commands
import discord

from views import Paginator

def setup(bot):
    @bot.command(name='users')
    async def users(ctx):
        # Create the cache directory if it doesn't exist
        if not os.path.exists('cache'):
            os.makedirs('cache')

        # Define the path to the JSON file
        cache_file = 'cache/rym-cache.json'

        # Load the existing data
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        # Prepare the user list for pagination
        rym_url = f"https://rateyourmusic.com/~"
        user_list = [f"<@{user_id}>: [{username}]({rym_url}{username})" for user_id, username in data.items()]
        embeds = []
        embed_description = ""

        for i, user_info in enumerate(user_list, start=1):
            embed_description += f"{user_info}\n"
            if i % 10 == 0 or i == len(user_list): 
                embed = discord.Embed(title="RYM Users", description=embed_description, color=discord.Color.blue())
                embeds.append(embed)
                embed_description = ""

        # Send the user list using the Paginator view
        view = Paginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @users.error
    async def users_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("No users found.")
