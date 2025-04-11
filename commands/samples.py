import time
import discord

from API.genius_search import *
from API.search_lastfm import get_lastfm_track
from views import Paginator

def setup(bot):
    @bot.command(name='samples')
    async def samples(ctx):
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
            await message.channel.send('Please provide a track or use `!setfm` to set your last.fm account.')
            return

    track_info = get_track_samples(track_name)
    if track_info.get("samples") or track_info.get("sampled_in") or track_info.get("interpolates") or track_info.get("interpolated_by"):
        artist_name = track_info.get("artist_name", "")
        track_name = track_info.get("track_name", "")
        release_year = track_info.get("release_year", "")
        genius_url = track_info.get("genius_url", "")
        cover_url = track_info.get("cover_url", "")

        embed_title = f"{artist_name} - {track_name} ({release_year})"
        embed_color = discord.Color.blue()
        embeds = []
        sample_in_embeds = []

        if len(track_info.get("samples")) > 0 or len(track_info.get("interpolates")) > 0:
            samples = track_info.get("samples", []) + track_info.get("interpolates", [])
        else:
            samples = ['No samples or interpolations found.']
        
        samples_pages = [samples[i:i + 5] for i in range(0, len(samples), 5)]

        for i, page in enumerate(samples_pages):
            embed_description = "\n".join(f" - {track}" for track in page)
            embed = discord.Embed(title=embed_title, description=embed_description, url=genius_url, color=embed_color)
            embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(samples_pages)}")
            if cover_url:
                embed.set_thumbnail(url=cover_url)
            embeds.append(embed)

        if track_info.get("sampled_in") or track_info.get("interpolated_by"):
            sampled_in = track_info.get("sampled_in", []) + track_info.get("interpolated_by")
            sampled_in_pages = [sampled_in[i:i + 5] for i in range(0, len(sampled_in), 5)]

            embed_color = discord.Color.green()
            for i, page in enumerate(sampled_in_pages):
                embed_description = "\n".join(f" - {track}" for track in page)
                embed = discord.Embed(title=embed_title, description=embed_description, url=genius_url, color=embed_color)
                embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(sampled_in_pages)}")
                if cover_url:
                    embed.set_thumbnail(url=cover_url)
                sample_in_embeds.append(embed)

        await message.channel.send(embed=embeds[0], view=Paginator(embeds, sample_in_embeds, action='samples'))
    else:
        await message.channel.send(f'**{track_name.title()}** samples not found.')