import time
import discord
from views import Paginator
from API.album_cache import *


def setup(bot):
    @bot.command(name='mosthatedreleases')
    async def mosthatedreleases(ctx):
        async with ctx.message.channel.typing():
            await most_hated_releases(ctx)
            time.sleep(5)

    @bot.command(name='mhr')
    async def mlr(ctx):
        async with ctx.message.channel.typing():
            await most_hated_releases(ctx)
            time.sleep(5)

async def most_hated_releases(message):
    most_loved = get_most_loved_hated_releases('disliked')
    leaderboard = []

    for idx, album in enumerate(most_loved, start=1):
        release_name = album.get('release_name')
        artist_name = album.get('artist_name')
        link = album.get('link')
        liked_users_count = len(album.get('disliked_users', []))
        leaderboard.append(f"{idx}. [{artist_name} - {release_name}]({link}) ({liked_users_count})")

    # Split leaderboard into pages of 10 entries each
    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []
    most_loved_image_url = most_loved[0].get('album_cover_url') if most_loved and 'album_cover_url' in most_loved[0] else None

    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.red()
        embed = discord.Embed(title="Most Hated Releases", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        if i == 0 and most_loved_image_url:
            embed.set_thumbnail(url=most_loved_image_url)
        embeds.append(embed)

    sent_message = await message.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
