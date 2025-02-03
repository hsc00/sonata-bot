import time
from API.artist_cache import *
from API.search_lastfm import check_user_lastfm_cache, get_last_played
from config import lastfm_api_key
import discord
from views import Paginator

def setup(bot):
    @bot.command(name='wholikedartist')
    async def wholiked(ctx):
        async with ctx.message.channel.typing():
            await who_liked_artist(ctx.message)
            pass
            time.sleep(5)

    @bot.command(name='wla')
    async def wl(ctx):
        await who_liked_artist(ctx.message)
        pass
        time.sleep(5)

async def who_liked_artist(message):
    artist = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not artist:
        last_fm_username = check_user_lastfm_cache(message.author.id)
        # Check if the user's last.fm username is stored
        if last_fm_username is not None:
            artist = get_last_played(last_fm_username, lastfm_api_key, 'artist')
        else:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    result = get_artist_from_cache(artist, increment_request_count=False)
    if result:
        pages = [result['liked_users'][i:i + 10] for i in range(0, len(result['liked_users']), 10)]
        artist_name = result.get('artist_name')
        link = result.get('link')

        embeds = []
        embed_title = f"{artist_name} Lovers"
        for i, page in enumerate(pages):
            embed_description = "\n".join(f"- <@{liked_users}>" for liked_users in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=link)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
            embeds.append(embed)
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await message.channel.send("No likes found.")