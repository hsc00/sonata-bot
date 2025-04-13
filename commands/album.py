import discord
import time
from datetime import datetime
import re
import urllib

from views import *
from config import *
from API.rym_search import search_rym_release
from API.rympy_rating import *
from API.setlist_search import *
from API.search_lastfm import get_lastfm_track


def setup(bot):
    @bot.command(name='album')
    async def album(ctx):
        async with ctx.channel.typing():
            await process_release_link_or_text(ctx.message)
        time.sleep(5)

    @bot.command(name='ab')
    async def ab(ctx):
        async with ctx.channel.typing():
            await process_release_link_or_text(ctx.message)
        time.sleep(5)

def extract_rym_info_from_link(url):
    parts = url.split('/')
    if len(parts) >= 5 and parts[3] == "release":
        if len(parts) >= 6:
            release_name_with_hyphens = parts[-2]
            artist_name_with_hyphens = parts[-3]
            return {
                "artist_name": artist_name_with_hyphens.replace("-", " "),
                "release_name": release_name_with_hyphens.replace("-", " ")
            }
    return None

async def process_release_link_or_text(message):
    release_query = message.content
    if 'https://rateyourmusic.com/release/' not in release_query:
        content_parts = release_query.split(' ', 1)
        if len(content_parts) > 1:
            release_query = content_parts[1]
        else:
            release_query = get_lastfm_track(message.author.id, 'release')
            # Check if the user's last.fm username is stored
            if release_query is None:
                await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
                return
    else:
        #clean message to get only the link
        match = re.search(r'(https?://)?(www\.)?rateyourmusic.com/.+', release_query)
        release_query = match.group(0)
    # perform a google search
    search_result = search_rym_release(release_query)
    
    embed_color = discord.Color.blue()

    if not search_result:
        if "rateyourmusic.com" in release_query.lower():
            rym_info = extract_rym_info_from_link(release_query)
            if rym_info:
                artist_name = rym_info['artist_name'].title()
                release_name = rym_info['release_name'].title()
                embed_title = f"{artist_name} - {release_name}"
                link = release_query
            else:
                await message.reply(f'Release link not found :/')
        else:
            embed_title = release_query.title()
            encoded_query = urllib.parse.quote(release_query)
            link = f"https://rateyourmusic.com/search?searchtype=a&searchterm={encoded_query}&searchtype="

        embed = discord.Embed(title=embed_title, url=link, color=embed_color)
        embed.set_footer(text=f"Requested by {message.author.name}")
        sent_message = await message.channel.send(embed=embed)
 
        view = RYMViewReleases(embed, original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name)
        view.link = link

        await sent_message.edit(view=view)
        return

    if search_result and search_result.get('artist_name'):
        artist_name = search_result['artist_name']
        release_name = search_result['release_name']
        release_year = search_result['release_year']
        genres = search_result['genres']
        rating_value = search_result['rating_value']
        formatted_rating_count = search_result['formatted_rating_count']
        best_album_position = search_result['best_album_position']
        all_time_album_position = search_result['all_time_album_position']
        performers = search_result['performers']

        if search_result.get('album_cover_url'):
            album_cover_url = search_result.get('album_cover_url')
        elif search_result.get('rym_cover_url'):
            album_cover_url = search_result.get('rym_cover_url')
        else:
            album_cover_url = None


        album_wiki = search_result['album_wiki']
        streaming_links = search_result['streaming_links']
        link = search_result['link']
        likes = len(search_result.get('liked_users', []))
        dislikes = len(search_result.get('disliked_users', []))

        embed_title = f"{artist_name} - {release_name} ({release_year})"
        if rating_value == "No Rating" or formatted_rating_count == "No Ratings":
            embed_description = ""
        else:    
            embed_description = f"*{genres}*\n\n**{rating_value}** ⭐ from **{formatted_rating_count}** ratings"

        if best_album_position:
            if not best_album_position.isdigit():
                match = re.search(r'#(\d+)', best_album_position)
                if match:
                    best_album_number = int(match.group(1))
            else:
                best_album_number = int(best_album_position)

            embed_description += f"\n#**{best_album_number}** of [{release_year}](https://rateyourmusic.com/charts/top/album/{release_year}/)"

        if all_time_album_position:
            if not all_time_album_position.isdigit():
                match = re.search(r'#(\d+)', all_time_album_position)
                if match:
                    all_time_album_number = int(match.group(1))
            else:
                all_time_album_number = int(all_time_album_position)

            embed_description += f", #**{all_time_album_number}** [overall](https://rateyourmusic.com/charts/top/album/all-time/)"
            embed_color = (
                discord.Color.gold() if all_time_album_number <= 250 else
                discord.Color.from_rgb(214, 214, 214) if all_time_album_number <= 1000 else
                discord.Color.from_rgb(151, 117, 71) if all_time_album_number > 1000 else
                embed_color
            )
        if rating_value == "No Rating":
            embed_color = discord.Color.default()
        elif float(rating_value) < 2.50:
            embed_color = discord.Color.red()
        if release_year != "Unknown Year" and int(release_year) == datetime.now().year:
            embed_color = discord.Color.green()

        embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
        if album_cover_url:
            embed.set_thumbnail(url=album_cover_url)

        embed.set_footer(text=f"Requested by {message.author.name}")
        sent_message = await message.channel.send(embed=embed)
 
        view = RYMViewReleases(album_wiki, embed, likes=likes, dislikes=dislikes, original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name, streaming_links=streaming_links, performers=performers)
        view.link = link

        await sent_message.edit(view=view)
    else:
        if "rateyourmusic.com" in release_query.lower():
            await message.reply(f'Release link retrieved a weird error :/')
        else:
            await message.reply(f'Search for **{release_query}** retrieved a weird error :/')