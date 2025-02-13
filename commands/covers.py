import time
import discord

from API.genius_search import *
from API.search_lastfm import get_lastfm_track
from views import Paginator

def setup(bot):
    @bot.command(name='covers')
    async def covers(ctx):
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
        if track_name is None:
            await message.reply('Please provide a track or use `!setfm` to set your last.fm account.')

    track_info = get_track_covers(track_name)
    if track_info.get("cover_of") or track_info.get("covered_by"):
        artist_name = track_info.get("artist_name", "")
        track_name = track_info.get("track_name", "")
        release_year = track_info.get("release_year", "")
        genius_url = track_info.get("genius_url", "")
        cover_url = track_info.get("cover_url", "")
        cover_of = track_info.get("cover_of", [])
        covered_by = track_info.get("covered_by", [])

        covered_by_page = [covered_by[i:i + 5] for i in range(0, len(covered_by), 5)]
        cover_of_page = [cover_of[i:i + 5] for i in range(0, len(cover_of), 5)]

        embed_title = f"{artist_name} - {track_name} ({release_year})"
        embed_color = discord.Color.blue()
        embeds = []
        for i, page in enumerate(covered_by_page):
            embed_description = "\n".join(f" - {track}" for track in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=genius_url, color=embed_color)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(covered_by_page)}")
            if cover_url:
                embed.set_thumbnail(url=cover_url)
            embeds.append(embed)

        cover_of__embeds = []
        embed_color = discord.Color.green()
        for i, page in enumerate(cover_of_page):
            embed_description = "\n".join(f" - {track}" for track in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=genius_url, color=embed_color)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(cover_of_page)}")
            if cover_url:
                embed.set_thumbnail(url=cover_url)
            cover_of__embeds.append(embed)

        await message.channel.send(embed=embeds[0], view=Paginator(embeds, cover_of__embeds, action='covers'))
    else:
        await message.channel.send(f'**{track_name.title()}** covers not found.')