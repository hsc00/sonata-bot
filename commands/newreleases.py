import json
import os
import requests
import asyncio
from datetime import datetime
from utils.text_formatters import rym_release_url_creator
from views import *
from bs4 import BeautifulSoup
from API.rym_search import search_rym_release
import discord

CACHE_FILE = "cache/new_releases.json"
SPUTNIK_URL = "https://www.sputnikmusic.com/newreleases.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def setup(bot):
    @bot.command(name='new', aliases=['newreleases'])
    async def newreleases(ctx):
        await get_new_releases(ctx)

def load_cache():
    """Load the cache file or initialize an empty list."""
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'w') as file:
            json.dump([], file)

    with open(CACHE_FILE, 'r') as file:
        return json.load(file)

def update_cache(artist_name, release_name):
    """Update the cache with new releases."""
    shown_albums = load_cache()
    album_identifier = f"{artist_name} - {release_name}"

    if album_identifier in shown_albums:
        return True

    shown_albums.append(album_identifier)
    with open(CACHE_FILE, 'w') as file:
        json.dump(shown_albums, file, indent=4) 

    return False

async def fetch_new_releases():
    """Fetch and parse new releases from SputnikMusic."""
    try:
        response = requests.get(SPUTNIK_URL, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        return soup.find_all("td", class_="hi")

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return []

async def get_new_releases(ctx):
    """Fetch and process new releases without repeating cached ones."""
    releases_table = await fetch_new_releases()
    shown_albums = load_cache() 

    async with ctx.typing():  # Keep typing indicator active while fetching
        for release in releases_table:
            artist_data = release.find("font", color="#111111")
            album_data = release.find("font", color="#555555")

            if artist_data and album_data:
                artist_name = artist_data.find("b").get_text(strip=True)
                release_name = album_data.get_text(strip=True)
                album_identifier = f"{artist_name} - {release_name}"

                if album_identifier in shown_albums:
                    continue

                await process_release(ctx, artist_name, release_name)

                # Only after posting, add to cache
                shown_albums.append(album_identifier)
                with open(CACHE_FILE, 'w') as file:
                    json.dump(shown_albums, file, indent=4)

                # Wait 5 seconds, only for new releases
                await asyncio.sleep(5)

async def process_release(ctx, artist_name, release_name):
    """Process and send release data to Discord before updating cache."""
    
    rym_data = search_rym_release(f"{artist_name} - {release_name}")
    embed_color = discord.Color.green()

    if rym_data and rym_data.get('artist_name'):
        # Process releases with RYM data
        artist_name = rym_data['artist_name']
        release_name = rym_data['release_name']
        embed_title = f"{artist_name} - {release_name}"
        embed_description = f"*{rym_data['genres']}*\n\n**{rym_data['rating_value']}** ⭐ from **{rym_data['formatted_rating_count']}** ratings" if rym_data['rating_value'] != "No Rating" else ""

        album_cover_url = rym_data.get('album_cover_url') or rym_data.get('rym_cover_url')
        embed = discord.Embed(title=embed_title, description=embed_description, url=rym_data['link'], color=embed_color)

        if album_cover_url:
            embed.set_thumbnail(url=album_cover_url)

        embed.set_footer(text="Source: Sputnikmusic")
        sent_message = await ctx.channel.send(embed=embed)
        
        view = RYMViewReleases(
            rym_data['album_wiki'], embed, likes=len(rym_data.get('liked_users', [])), dislikes=len(rym_data.get('disliked_users', [])),
            original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name,
            streaming_links=rym_data['streaming_links'], performers=rym_data['performers']
        )
        view.link = rym_data['link']

        await sent_message.edit(view=view)

    else:
        # Handles releases that DON'T have RYM data
        embed_title = f"{artist_name} - {release_name}"
        embed = discord.Embed(title=embed_title, url=rym_release_url_creator(artist_name, release_name), color=embed_color)
        embed.set_footer(text="Source: Sputnikmusic")

        sent_message = await ctx.channel.send(embed=embed)
        view = RYMViewReleases(original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name)
        await sent_message.edit(view=view)

    # After sending, update the cache
    update_cache(artist_name, release_name)
