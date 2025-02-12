import time
import discord

from API.genius_search import *
from API.search_lastfm import get_lastfm_track
from views import RYMViewTracks

def setup(bot):
    @bot.command(name='trackinfo')
    async def trackinfo(ctx):
        async with ctx.message.channel.typing():
            await check_genius(ctx.message)
            time.sleep(5)

    @bot.command(name='tr')
    async def tr(ctx):
        async with ctx.message.channel.typing():
            await check_genius(ctx.message)
            time.sleep(5)

async def check_genius(message):
    song_query = message.content
    content_parts = song_query.split(' ', 1)
    if len(content_parts) > 1:
        track_name = content_parts[1]
    else:
        track_name = get_lastfm_track(message.author.id, 'track')
        # Check if the user's last.fm username is stored
        if track_name is None:
            await message.channel.send('Please provide a track or use `!setfm` to set your last.fm account.')
            return
    track_info = get_track_info(track_name)
    if track_info.get('artist_name'):
        artist_name = track_info.get("artist_name", "")
        track_name = track_info.get("track_name", "")
        release_year = track_info.get("release_year", "")
        genius_url = track_info.get("genius_url", "")
        cover_url = track_info.get("cover_url", "")
        credits = track_info.get("credits", "")
        wiki = track_info.get("wiki", "")
        streaming_links = track_info.get("links", "")

        embed_title = f"{artist_name} - {track_name} ({release_year})"
        embed_description = wiki
        embed_color = discord.Color.blue()

        embed = discord.Embed(title=embed_title, description=embed_description, url=genius_url, color=embed_color)
        if cover_url:
            embed.set_thumbnail(url=cover_url)
        embed.set_footer(text=f"Requested by {message.author.name}")
        sent_message = await message.channel.send(embed=embed)
 
        view = RYMViewTracks(embed, wiki, credits, streaming_links)
        await sent_message.edit(view=view)
    else:
        await message.channel.send(f'**{track_name.title()}** info not found.')