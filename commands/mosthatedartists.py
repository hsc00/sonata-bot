import time
import discord
from views import Paginator
from API.artist_cache import *


def setup(bot):
    @bot.command(name='mosthatedartists')
    async def mosthatedartists(ctx):
        async with ctx.message.channel.typing():
            await most_hated_artists(ctx)
            time.sleep(5)

    @bot.command(name='mha')
    async def mha(ctx):
        async with ctx.message.channel.typing():
            await most_hated_artists(ctx)
            time.sleep(5)

async def most_hated_artists(message):
    most_loved = get_most_loved_hated_artists('disliked')
    leaderboard = []

    for idx, artist in enumerate(most_loved, start=1):
        artist_name = artist.get('artist_name')
        link = artist.get('link')
        liked_users_count = len(artist.get('disliked_users', []))
        leaderboard.append(f"{idx}. [{artist_name}]({link}) ({liked_users_count})")

    # Split leaderboard into pages of 10 entries each
    pages = [leaderboard[i:i + 10] for i in range(0, len(leaderboard), 10)]
    embeds = []
    most_loved_image_url = most_loved[0].get('artist_img_url') if most_loved and 'artist_img_url' in most_loved[0] else None

    for i, page in enumerate(pages):
        embed_description = "\n".join(page)
        embed_color = discord.Color.green()
        embed = discord.Embed(title="Most Hated Artists", description=embed_description, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        if i == 0 and most_loved_image_url:
            embed.set_thumbnail(url=most_loved_image_url)
        embeds.append(embed)

    sent_message = await message.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
