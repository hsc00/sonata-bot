import json
import os
from discord.ext import commands

def setup(bot):
    @bot.command(name='setrym')
    async def setrym(ctx, rym_username: str):
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

        # Update the data with the new user information
        data[str(ctx.author.id)] = rym_username

        # Save the updated data to the JSON file
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=4)

        # Create the hyperlink for the Last.fm username
        rym_profile_url = f"https://rateyourmusic.com/~{rym_username}"
        await ctx.reply(f"{ctx.author.mention} RYM has been set to [{rym_username}]({rym_profile_url})")

    @setrym.error
    async def setrym_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("You need to provide a RYM username. Usage: `!setrym <rym_username>`")
