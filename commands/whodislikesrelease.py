import time
from API.album_cache import *
from API.search_lastfm import get_lastfm_track
import discord
from views import Paginator

def setup(bot):
    @bot.command(name='whodislikesrelease')
    async def whodislikesrelease(ctx):
        async with ctx.message.channel.typing():
            await who_disliked_release(ctx.message)
            pass
            time.sleep(5)

    @bot.command(name='wdr')
    async def wdr(ctx):
        await who_disliked_release(ctx.message)
        pass
        time.sleep(5)

async def who_disliked_release(message):
    release = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not release:
        release = get_lastfm_track(message.author.id, 'release')
        # Check if the user's last.fm username is stored
        if release is None:
            await message.channel.send('Please provide a release or use `!setfm` to set your last.fm account.')
            return
    result = get_album_from_cache(release, increment_request_count=False)
    if result and len(result['disliked_users']) > 0:
        pages = [result['disliked_users'][i:i + 10] for i in range(0, len(result['disliked_users']), 10)]
        artist_name = result.get('artist_name')
        release_name = result.get('release_name')
        link = result.get('link')
        embeds = []
        embed_title = f"{artist_name} - {release_name} Haters"
        for i, page in enumerate(pages):
            embed_description = "\n".join(f"- <@{disliked_users}>" for disliked_users in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=link)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
            embeds.append(embed)
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await message.channel.send(f"No dislikes found for **{release}**")