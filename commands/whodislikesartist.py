import time
from API.artist_cache import *
from API.search_lastfm import get_lastfm_track
import discord
from views import Paginator

def setup(bot):
    @bot.command(name='whodislikesartist')
    async def whodislikesartist(ctx):
        async with ctx.message.channel.typing():
            await who_disliked_artist(ctx.message)
            pass
            time.sleep(5)

    @bot.command(name='wda')
    async def wda(ctx):
        await who_disliked_artist(ctx.message)
        pass
        time.sleep(5)

async def who_disliked_artist(message):
    artist = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not artist:
        artist = get_lastfm_track(message.author.id, 'artist')
        # Check if the user's last.fm username is stored
        if artist is None:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    result = get_artist_from_cache(artist, increment_request_count=False)
    if len(result['disliked_users']) > 0:
        pages = [result['disliked_users'][i:i + 10] for i in range(0, len(result['disliked_users']), 10)]
        artist_name = result.get('artist_name')
        link = result.get('link')
        embeds = []
        embed_title = f"{artist_name} Haters"
        for i, page in enumerate(pages):
            embed_description = "\n".join(f"- <@{liked_users}>" for liked_users in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=link)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
            embeds.append(embed)
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await message.channel.send("No dislikes found.")