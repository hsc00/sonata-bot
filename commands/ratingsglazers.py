import discord
from API.ratings_cache import get_users_by_average_rating
from utils.discord_data_functions import get_user_avatar
from utils.text_formatters import format_count
from views import Paginator


def setup(bot):
    @bot.command(name='ratingsglazers', aliases=['rg'])
    async def ratingsglazers(ctx):
        async with ctx.message.channel.typing():
            await get_ratings_glazers(ctx)


async def get_ratings_glazers(ctx):
    user_weighted_ratings, avg_rating = get_users_by_average_rating("best")

    if not user_weighted_ratings:
        await ctx.send("No user rankings available.")
        return

    embeds = []
    total_users = len(user_weighted_ratings)

    for i in range(0, total_users, 10):
        chunk = user_weighted_ratings[i:i+10]
        embed_description = "\n".join([f"{i+index+1}. <@{user[0]}> {user[3]} ⭐ • ({format_count(user[4])})" for index, user in enumerate(chunk)])
        
        embed = discord.Embed(title=f"{ctx.guild.name} Glazers Ranking", description=embed_description, color=discord.Color.green())
        avatar_url = await get_user_avatar(ctx, chunk[0][0]) if chunk else None
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.set_footer(text=f"{ctx.guild.name} Average Rating is {avg_rating} \u00A0 • \u00A0 Page {len(embeds)+1}/{-(-total_users//10)}")
        embeds.append(embed)

    paginator = Paginator(embeds)
    await ctx.send(embed=embeds[0], view=paginator)
