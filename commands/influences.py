from API.influences_search import *
from API.search_lastfm import get_lastfm_track
from views import Paginator
import time
import discord

def setup(bot):
    @bot.command(name='influences')
    async def influences(ctx):
        async with ctx.message.channel.typing():
            await check_influences(ctx.message)
            time.sleep(5)

    @bot.command(name='inf')
    async def inf(ctx):
        async with ctx.message.channel.typing():
            await check_influences(ctx.message)
            time.sleep(5)

async def check_influences(message):
    artist = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not artist:
        artist = get_lastfm_track(message.author.id, 'artist')
        # Check if the user's last.fm username is stored
        if artist is None:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    result = await fetch_artist_data(artist, 'influences')
    influences = result['data']
    artist_image = result['artist_image']

    if influences:
        pages = [influences[i:i + 10] for i in range(0, len(influences), 10)]
        embeds = []
        embed_title = f"{artist.title()} Influences"
        for i, page in enumerate(pages):
            embed_description = "\n".join(f"- [{name}](https://rateyourmusic.com/artist/{name.replace(' ', '-').lower()})" for name in page)
            embed = discord.Embed(title=embed_title, description=embed_description)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
            embed.set_thumbnail(url=artist_image)
            embeds.append(embed)
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await message.channel.send(f"No data found for **{artist.title()}**")


async def fetch_artist_data(artist, list_type):
    cached_data = load_from_cache(artist.lower())
    if cached_data and list_type in cached_data:
        data = cached_data
    else:
        data = get_lists(artist.replace(" ", "+"))
        save_to_cache(artist, data)

    return {
        "data": data[list_type],
        "artist_image": data.get('artist_image')
    }
