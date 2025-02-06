import time
from API.album_cache import *
from API.search_lastfm import get_lastfm_track
import discord
from views import Paginator

def setup(bot):
    @bot.command(name='wholikesrelease')
    async def wholikesrelease(ctx):
        async with ctx.message.channel.typing():
            await who_liked_release(ctx.message)
            pass
            time.sleep(5)

    @bot.command(name='wlr')
    async def wlr(ctx):
        await who_liked_release(ctx.message)
        pass
        time.sleep(5)

async def who_liked_release(message):
    release = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not release:
        release = get_lastfm_track(message.author.id, 'release')
        # Check if the user's last.fm username is stored
        if release is None:
            await message.channel.send('Please provide a release or use `!setfm` to set your last.fm account.')
            return
    result = get_album_from_cache(release, increment_request_count=False)
    if result and len(result['liked_users']) > 0:
        pages = [result['liked_users'][i:i + 10] for i in range(0, len(result['liked_users']), 10)]
        artist_name = result.get('artist_name')
        release_name = result.get('release_name')
        link = result.get('link')
        embeds = []
        embed_title = f"{artist_name} - {release_name} Lovers"
        for i, page in enumerate(pages):
            embed_description = "\n".join(f"- <@{liked_users}>" for liked_users in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=link)
            if result['album_cover_url']:
                embed.set_thumbnail(url=result['album_cover_url'])
            elif result['rym_cover_url']:
                embed.set_thumbnail(url=result['rym_cover_url'])
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
            embeds.append(embed)
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await message.channel.send(f"No likes found for **{release}**")