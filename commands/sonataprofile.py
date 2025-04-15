from discord.ext import commands
from API.ratings_cache import get_rym_user_info
from utils.discord_data_functions import get_user_avatar
from utils.rym_data_functions import rym_user_data
import discord


def setup(bot):
    @bot.command(name='sonataprofile', aliases=['spr'])
    async def profile(ctx, rym_user_id: str = None):
        data, user_id, username, link = rym_user_data(ctx, rym_user_id)
        if data and username and user_id:
            embed = await create_profile_embed(ctx, user_id, username, link)
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have a RYM profile set. Use the `!setrym <rym_username>` command to set it.")

    @profile.error
    async def profile_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("No users found.")

async def create_profile_embed(ctx, user_id, username, link):
    avatar_url = await get_user_avatar(ctx, user_id)
    average_rating, ratings_number, ratings_chart, most_rated_decade, most_rated_year, best_rated_decade, best_rated_year = get_rym_user_info(ctx, user_id)

    if ratings_number < 1:
        embed_description = "This is your simple bio because there are no ratings imported."
    else:
        embed_description = f"Average Rating • **{average_rating}** ⭐ • **{ratings_number}** ratings\n\n{ratings_chart}\n\nMost Rated Decade • **{most_rated_decade}**"
        embed_description += f"\nMost Rated Year • **{most_rated_year}\n**Best Rated Decade • **{best_rated_decade}**\nBest Rated Year • **{best_rated_year}**"
    
    embed = discord.Embed(title=f"{username}", url=link, description=embed_description, color=discord.Color.random())
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    
    return embed
