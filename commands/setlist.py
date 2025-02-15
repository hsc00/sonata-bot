from views import *
from API.setlist_search import *
from API.search_lastfm import get_lastfm_track

def setup(bot):
    @bot.command(name='setlist')
    async def setlist_command(ctx):
        async with ctx.message.channel.typing():
            await process_setlist(ctx.message)

    @bot.command(name='st')
    async def st_command(ctx):
        async with ctx.message.channel.typing():
            await process_setlist(ctx.message)

async def process_setlist(message):
    content_parts = message.content.split(' ', 1)
    if len(content_parts) > 1:
        artist_name = content_parts[1]
    else:
        artist_name = get_lastfm_track(message.author.id, 'artist')
        if artist_name is None:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    
    setlist = get_setlist(artist_name)
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

    embed_title = f"{artist_name} - {concert_name}"
    embed_color = discord.Color.blue()

    embeds = []
    for i, page in enumerate(pages):
        embed_description = f"**{city_name}, {country_name}**\n{concert_date}\n\n"
        embed_description += "\n".join(f" - {track}" for track in page)
        embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
        embeds.append(embed)

    await message.channel.send(embed=embeds[0], view=Paginator(embeds))
