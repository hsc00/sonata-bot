import html
import time
import discord
from API.ratings_cache import get_most_rated_artists
from utils.text_formatters import get_user_id, rym_user_url_creator
from views import Paginator
from API.album_cache import *


def setup(bot):
    @bot.command(name='mostratedartists', aliases=['mra'])
    async def mostratedalbums(ctx):
        async with ctx.message.channel.typing():
            await most_rated_artists(ctx)
            time.sleep(5)

async def most_rated_artists(ctx):
    release_query, user_id = get_user_id(ctx.message.content)
    most_rated = get_most_rated_artists(user_id)
    user_checked = await ctx.guild.fetch_member(user_id) if user_id else None
    leaderboard = []

    for idx, album in enumerate(most_rated, start=1):
        if isinstance(album, dict) and album.get('artist_name') is not None:
            artist_name = html.unescape(album.get('artist_name'))
            link = album.get('link')
            rating_count = album.get('rating_count', 0)
            leaderboard.append(f"{idx}. [{artist_name}]({link}) ({rating_count})")
        else:
            await ctx.channel.send(f"<@{user_id}> doesn't have any rated albums... Have you imported your ratings?")
            return

    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []

    link = rym_user_url_creator(user_id if user_id else None)
    
    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.green()
        if user_checked:
            embed = discord.Embed(title=f"{user_checked.name} Most Rated Artists", url=link, description=embed_description, color=embed_color)
        else:
            embed = discord.Embed(title=f"{ctx.guild.name} Most Rated Artists", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {ctx.author.display_name} • Page {i + 1}/{len(pages)}")
        embeds.append(embed)

    sent_message = await ctx.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
