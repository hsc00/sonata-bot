import time
import discord
from API.ratings_cache import get_most_rated_releases
from views import Paginator
from API.album_cache import *


def setup(bot):
    @bot.command(name='mostratedalbums', aliases=['mrab'])
    async def mostratedalbums(ctx):
        async with ctx.message.channel.typing():
            await most_rated_albums(ctx)
            time.sleep(5)

async def most_rated_albums(message):
    most_rated = get_most_rated_releases()
    leaderboard = []

    for idx, album in enumerate(most_rated, start=1):
        release_name = album.get('release_name')
        artist_name = album.get('artist_name')
        link = album.get('link')
        rating_count = album.get('rating_count', 0)
        leaderboard.append(f"{idx}. [{artist_name} - {release_name}]({link}) ({rating_count})")

    # Split leaderboard into pages of 10 entries each
    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []
    most_loved_image_url = most_rated[0].get('album_cover_url') if most_rated and 'album_cover_url' in most_rated[0] else None

    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.green()
        embed = discord.Embed(title="Most Rated Releases", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        if i == 0 and most_loved_image_url:
            embed.set_thumbnail(url=most_loved_image_url)
        embeds.append(embed)

    sent_message = await message.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
