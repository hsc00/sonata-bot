import json
import os
from discord.ext import commands
import discord

from views import Paginator

def setup(bot):
    @bot.command(name='profile')
    async def profile(ctx, rym_user_id: str = None):
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

        async def create_profile_embed(user_id, username):
            try:
                user = await ctx.guild.fetch_member(user_id)
                avatar_url = user.avatar.url
            except discord.NotFound:
                avatar_url = None

            link = f"https://rateyourmusic.com/~{username}"
            embed_description = "An amazing bio will be here."
            embed = discord.Embed(title=f"{username}", url=link, description=embed_description, color=discord.Color.green())
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            return embed

        # Check if a specific user ID or mention is provided
        if rym_user_id:
            # Extract the user ID from the mention if necessary
            if rym_user_id.startswith('<@') and rym_user_id.endswith('>'):
                rym_user_id = rym_user_id[2:-1]
                if rym_user_id.startswith('!'):
                    rym_user_id = rym_user_id[1:]

            # Search for the specified user ID
            if rym_user_id in data:
                username = data[rym_user_id]
                embed = await create_profile_embed(rym_user_id, username)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No user found with the ID `{rym_user_id}`.")
        else:
            # Search for the user who made the prompt
            user_id = str(ctx.author.id)
            if user_id in data:
                username = data[user_id]
                embed = await create_profile_embed(user_id, username)
                await ctx.send(embed=embed)
            else:
                await ctx.send("You don't have a RYM profile set. Use the `!setrym <rym_username>` command to set it.")

    @profile.error
    async def profile_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("No users found.")
