import discord
from API.ratings_cache import get_ratings_ranking
from utils.discord_data_functions import get_user_avatar
from views import Paginator


def setup(bot):
    @bot.command(name='ratingsrank', aliases=['rr'])
    async def ratingsrank(ctx):
        async with ctx.message.channel.typing():
            await get_ratings_rank(ctx)


async def get_ratings_rank(ctx):
    top_users = get_ratings_ranking(ctx)

    if not top_users:
        await ctx.send("No user rankings available.")
        return

    embeds = []
    total_users = len(top_users)

    for i in range(0, total_users, 10):
        chunk = top_users[i:i+10]
        embed_description = "\n".join([f"{i+index+1}. <@{user[0]}> ({user[1]})" for index, user in enumerate(chunk)])
        
        embed = discord.Embed(title=f"{ctx.guild.name} Ratings Ranking", description=embed_description, color=discord.Color.random())
        avatar_url = await get_user_avatar(ctx, chunk[0][0]) if chunk else None
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.set_footer(text=f"Page {len(embeds)+1}/{-(-total_users//10)}")
        embeds.append(embed)

    paginator = Paginator(embeds)
    await ctx.send(embed=embeds[0], view=paginator)
