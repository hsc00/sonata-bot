from discord.ext import commands
import discord
from typing import Optional
from API.ratings_cache import get_rym_aoty
from utils.discord_data_functions import get_user_username
from utils.text_formatters import format_user_id
from views import Paginator


def setup(bot: commands.Bot):
    @bot.command(name='aoty')
    async def aoty(ctx: commands.Context, year: Optional[str] = None, user_id: Optional[str] = None):
        async with ctx.typing():
            await get_best_rated_releases(ctx, year, user_id)


async def get_best_rated_releases(ctx: commands.Context, year: Optional[str], user_id: Optional[str] = None):
    user_id = ctx.author.id if user_id is None else format_user_id(user_id)
    user_id = int(user_id)
    
    username = await get_user_username(ctx, user_id)
    
    sorted_albums, target_year, avg_rating, error = await get_rym_aoty(ctx, user_id, year, "best")  

    if not sorted_albums:
        await ctx.reply(error)
        return

    embeds = []
    
    for i in range(0, len(sorted_albums), 10):
        chunk = sorted_albums[i:i+10]
        embed_description = "\n".join([
            f"{i + index + 1}. [{album['artist_name']} - {album['release_name']}]({album['link']}) • **{album['release_rating']}** ⭐"
            for index, album in enumerate(chunk)
        ])
        
        embed = discord.Embed(
            title=f"{username.title()} Top {target_year} Releases",
            description=embed_description,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Your Average {target_year} Rating: {avg_rating} \u00A0 • \u00A0 Page {len(embeds)+1}/{-(-len(sorted_albums)//10)}")
        embeds.append(embed)

    paginator = Paginator(embeds)
    await ctx.send(embed=embeds[0], view=paginator)
