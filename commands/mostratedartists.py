import time
import discord
from API.ratings_cache import get_most_rated_artists, get_most_rated_releases
from views import Paginator
from API.album_cache import *


def setup(bot):
    @bot.command(name='mostratedartists', aliases=['mra'])
    async def mostratedalbums(ctx):
        async with ctx.message.channel.typing():
            await most_rated_artists(ctx)
            time.sleep(5)

async def most_rated_artists(message):
    most_rated = get_most_rated_artists()
    leaderboard = []

    for idx, album in enumerate(most_rated, start=1):
        artist_name = album.get('artist_name')
        link = album.get('link')
        rating_count = album.get('rating_count', 0)
        leaderboard.append(f"{idx}. [{artist_name}]({link}) ({rating_count})")

    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []

    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.green()
        embed = discord.Embed(title="Most Rated Artists", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        embeds.append(embed)

    sent_message = await message.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
