import config
from views import *
from API.setlist_search import *
from API.search_lastfm import check_user_lastfm_cache, get_last_played

def setup(bot):
    @bot.command(name='setlist')
    async def setlist_command(ctx):
        async with ctx.message.channel.typing():
            await process_setlist(ctx.message)
            time.sleep(5)

    @bot.command(name='st')
    async def st_command(ctx):
        async with ctx.message.channel.typing():
            await process_setlist(ctx.message)
            time.sleep(5)

async def process_setlist(message):
    content_parts = message.content.split(' ', 1)
    if len(content_parts) > 1:
        artist_name = content_parts[1]
    else:
        last_fm_username = check_user_lastfm_cache(message.author.id)
        # Check if the user's last.fm username is stored
        if last_fm_username is not None:
            artist_name = get_last_played(last_fm_username, config.lastfm_api_key, 'artist')
        else:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    setlist = get_setlist(artist_name, config.setlist_api_key)
    if not setlist or 'error' in setlist:
        await message.channel.send('Artist not found or timeout. Try again.')
        return

    artist_name = setlist['artist_name']
    link = setlist['url']
    concert_name = setlist['concert_name']
    city_name = setlist['city_name']
    country_name = setlist['country_name']
    concert_date = setlist['concert_date']
    tracks_played = setlist['tracks_played']

    if not tracks_played:
        await message.channel.send(f'No tracks found in the setlist. You can be the one adding them [here]({link}).')
        return

    pages = [tracks_played[i:i + 10] for i in range(0, len(tracks_played), 10)]

    embeds = []
    embed_title = f"{artist_name} (Last Setlist)"
    for i, page in enumerate(pages):
        embed_description = f"**{concert_name}, {city_name}, {country_name}**\n{concert_date}\n\n"
        embed_description += "\n".join(f" - {track}" for track in page)
        embed = discord.Embed(title=embed_title, description=embed_description, url=link)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        embeds.append(embed)

    sent_message = await message.channel.send(embed=embeds[0])
    view = Paginator(embeds)
    await sent_message.edit(embed=embeds[0], view=view)
