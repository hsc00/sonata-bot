import html
import time
import discord
from API.ratings_cache import get_best_worst_rated_releases
from views import Paginator
from API.album_cache import *
from utils.text_formatters import get_user_id, rym_user_url_creator


def setup(bot):
    @bot.command(name='worstratedreleases', aliases=['wrr'])
    async def worstratedreleases(ctx):
        async with ctx.message.channel.typing():
            await worst_rated_releases(ctx)
            time.sleep(2)


async def worst_rated_releases(ctx):
    release_query, user_id = get_user_id(ctx.message.content)
    worst_rated = get_best_worst_rated_releases('worst', user_id)
    user_checked = await ctx.guild.fetch_member(user_id) if user_id else None
    leaderboard = []

    for idx, album in enumerate(worst_rated, start=1):
        if isinstance(album, dict) and album.get('artist_name') is not None:
            artist_name = html.unescape(album.get('artist_name'))
            release_name = html.unescape(album.get('release_name'))
            link = album.get('link')
            average_rating = album.get('average_rating', 0)
            rating = album.get('rating', 0)
            total_ratings = album.get('total_ratings', 0)
            if user_id == None:
                leaderboard.append(f"{idx}. [{artist_name} - {release_name}]({link}) (**{average_rating}** ⭐ from **{total_ratings}** ratings)")
            else:
                leaderboard.append(f"{idx}. [{artist_name} - {release_name}]({link}) • **{rating}** ⭐")
        else:
            await ctx.channel.send(f"<@{user_id}> doesn't hate any release... Take notes!")
            return

    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []

    link = rym_user_url_creator(user_id if user_id else None)

    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.red()
        if user_checked:
            embed = discord.Embed(title=f"{user_checked.name} Worst Rated Releases", url=link, description=embed_description, color=embed_color)
        else:
            embed = discord.Embed(title=f"{ctx.guild.name} Worst Rated Releases", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {ctx.author.display_name} • Page {i + 1}/{len(pages)}")
        embeds.append(embed)

    sent_message = await ctx.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
