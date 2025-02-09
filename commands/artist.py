import discord
import time
import re

from views import *
from config import *
from API.rym_search import search_rym_artist
from API.rympy_rating import *
from API.setlist_search import *
from API.search_lastfm import get_lastfm_track

def setup(bot):
    @bot.command(name='artist')
    async def artist(ctx):
        async with ctx.channel.typing():
            await process_artist_link_or_text(ctx.message)
        time.sleep(5)

    @bot.command(name='a')
    async def a(ctx):
        async with ctx.channel.typing():
            await process_artist_link_or_text(ctx.message)
        time.sleep(5)


async def process_artist_link_or_text(message):
    artist_query = message.content
    if artist_query.startswith('!artist') or artist_query.startswith('!a'):
        content_parts = artist_query.split(' ', 1)
        if len(content_parts) > 1:
            artist_query = content_parts[1]
        else:
            artist_query = get_lastfm_track(message.author.id, 'artist')
            # Check if the user's last.fm username is stored
            if artist_query is None:
                await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
                return
    else:
        #clean message to get only the link
        match = re.search(r'(https?://)?(www\.)?rateyourmusic.com/.+', artist_query)
        artist_query = match.group(0)

    artist_info = search_rym_artist(artist_query)
    if artist_info:
        artist_name = artist_info['artist_name']
        founded_year = artist_info.get('founded_year') if artist_info.get('founded_year') != "Unknown" else ''
        genres = artist_info.get('genres')
        listeners = artist_info.get('listeners')
        similar_artists = artist_info.get('similar_artists')
        artist_img_url = artist_info.get('artist_img_url', artist_info.get('rym_img_url'))
        artist_summary = artist_info.get('summary')
        streaming_links = artist_info.get('streaming_links')
        link = artist_info.get('link')
        likes = len(artist_info.get('liked_users', []))
        dislikes = len(artist_info.get('disliked_users', []))

        embed_title = f"{artist_name}"
        embed_description = f"*{genres}*\n\nListeners: **{listeners}**\n {founded_year}\n\n {artist_summary}"
        embed_color = discord.Color.blue()
        embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
        if artist_img_url:
            embed.set_thumbnail(url=artist_img_url)

        embed.set_footer(text=f"Requested by {message.author.name}")
        sent_message = await message.channel.send(embed=embed)

        view = RYMViewArtists(artist_name, similar_artists, embed, likes=likes, dislikes=dislikes, original_message_id=sent_message.id, streaming_links=streaming_links, release_name=None)
        view.link = link

        await sent_message.edit(view=view)
    else:
        await message.channel.send('Artist not found.')