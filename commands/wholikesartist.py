import time
import discord
from API.rym_search import search_rym_artist
from views import Paginator
from API.artist_cache import *
from API.search_lastfm import get_lastfm_track

def setup(bot):
    @bot.command(name='wholikesartist')
    async def wholikesartist(ctx):
        async with ctx.message.channel.typing():
            await who_liked_artist(ctx.message)
            time.sleep(5)

    @bot.command(name='wla')
    async def wla(ctx):
        async with ctx.message.channel.typing():
            await who_liked_artist(ctx.message)
            time.sleep(5)

async def who_liked_artist(message):
    artist = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not artist:
        artist = get_lastfm_track(message.author.id, 'artist')
        # Check if the user's last.fm username is stored
        if artist is None:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    result = search_rym_artist(artist)
    if result and len(result['liked_users']) > 0:
        pages = [result['liked_users'][i:i + 10] for i in range(0, len(result['liked_users']), 10)]
        artist_name = result.get('artist_name')
        link = result.get('link')
        embeds = []
        embed_title = f"{artist_name} Lovers"
        for i, page in enumerate(pages):
            embed_description = "\n".join(f"- <@{liked_users}>" for liked_users in page)
            embed_color = discord.Color.green()
            embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
            if result['artist_img_url']:
                embed.set_thumbnail(url=result['artist_img_url'])
            embeds.append(embed)
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await message.channel.send(f"No likes found for **{artist}**")