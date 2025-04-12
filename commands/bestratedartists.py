import time
import discord
from API.ratings_cache import get_best_rated_artists
from views import Paginator
from API.album_cache import *


def setup(bot):
    @bot.command(name='bestratedartists', aliases=['bra'])
    async def bestratedartists(ctx):
        async with ctx.message.channel.typing():
            await best_rated_artists(ctx)
            time.sleep(5)

async def best_rated_artists(message):
    best_rated = get_best_rated_artists()
    leaderboard = []

    for idx, album in enumerate(best_rated, start=1):
        artist_name = album.get('artist_name')
        link = album.get('link')
        average_rating = album.get('average_rating', 0)
        unique_releases = len(album.get('unique_releases', 0))
        total_ratings = album.get('total_ratings', 0)
        leaderboard.append(f"{idx}. [{artist_name}]({link}) ({average_rating} from {unique_releases} releases)")

    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []

    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.green()
        embed = discord.Embed(title="Best Rated Artists", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        embeds.append(embed)

    sent_message = await message.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
