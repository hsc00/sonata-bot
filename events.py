import csv
import lzma
import pickle
import shutil
import discord
import requests
import time
from datetime import datetime
import re

from views import *
from config import *
from API.rym_search import search_rym_release, search_rym_artist
from API.rympy_rating import *
from API.setlist_search import *
from API.search_lastfm import get_lastfm_track

global ratings_cache
ratings_cache = dict()
bot_instance = None

try:
    with lzma.open('cache/ratings_cache.lzma', 'rb') as file:
        try:
            ratings_cache = pickle.load(file)
        except:
            ratings_cache = dict()
except FileNotFoundError:
    with lzma.open('cache/ratings_cache.lzma', 'wb') as file:
        pickle.dump(dict(), file)


async def on_message(message):
    if message.author == bot_instance.user:
        return
    if 'rateyourmusic.com/release/' in message.content and len(message.content.split('/')) > 5 or message.content.startswith('!album') or message.content.startswith('!ab'):
        async with message.channel.typing():
            await process_release_link_or_text(message)
        time.sleep(5)
    elif 'rateyourmusic.com/artist/' in message.content and len(message.content.split('/')) > 3 or message.content.startswith('!artist') or message.content.startswith('!a'):
        async with message.channel.typing():
            await process_artist_link_or_text(message)
        time.sleep(5)
    elif message.content == '!import' or message.content == '!i':
         await process_ratings_command(message)
    elif message.content.startswith('!wa'):
        #await process_who_knows_command(message)
        pass

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


# searches release on rym
async def process_release_link_or_text(message):
    release_query = message.content
    if release_query.startswith('!album') or release_query.startswith('!ab'):
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
    if not search_result:
        await message.channel.send('Release not found.')
        return

    if search_result:
        artist_name = search_result['artist_name']
        release_name = search_result['release_name']
        release_year = search_result['release_year']
        genres = search_result['genres']
        rating_value = search_result['rating_value']
        formatted_rating_count = search_result['formatted_rating_count']
        best_album_position = search_result['best_album_position']
        all_time_album_position = search_result['all_time_album_position']
        performers = search_result['performers']

        if search_result['album_cover_url']:
            album_cover_url = search_result['album_cover_url']
        else:
            album_cover_url = search_result['rym_cover_url']

        album_wiki = search_result['album_wiki']
        streaming_links = search_result['streaming_links']
        link = search_result['link']
        likes = len(search_result.get('liked_users', []))
        dislikes = len(search_result.get('disliked_users', []))

        embed_title = f"{artist_name} - {release_name} ({release_year})"
        embed_description = f"*{genres}*\n\n**{rating_value}** ⭐ from **{formatted_rating_count}** ratings"
        embed_color = discord.Color.blue()

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
        if float(rating_value) < 2.50:
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


def import_ratings(url):
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Request to ratings file failed.")
        return
    
    ratings_proto = list(csv.DictReader(response.text.splitlines()))
    ratings_list = []

    for row in ratings_proto:
        rating = Rating(
            id=row["RYM Album"],
            first_name=row[" First Name"],
            last_name=row["Last Name"],
            first_name_localized=row["First Name localized"],
            last_name_localized=row[" Last Name localized"],
            title=row["Title"],
            release_year=int(row["Release_Date"]) if row["Release_Date"] else None,
            rating=int(row["Rating"])/2 if row["Rating"] != "" else None,
            ownership=row["Ownership"],
            purchase_date=row["Purchase Date"],
            media_type=row["Media Type"],
            review=row.get(" Review")
        )
        ratings_list.append(rating)

        if rating.rating == 5:
            pass
        elif rating.rating <= 2:
            pass

    return ratings_list
    

async def process_ratings_command(message):
    global ratings_cache
    processed_message = message.content.split(' ')
    if len(processed_message) == 2:
        ratings_cache[str(message.author.id)] = import_ratings(url=processed_message[1])
    else:
        ratings_cache[str(message.author.id)] = import_ratings(url=message.attachments[0].url)
    await message.reply("Your ratings have been imported successfully.")
    print("SAVING RATINGS CACHE, DON'T CLOSE THE BOT")
    with lzma.open('cache/rating_cache_tmp.lzma', 'wb') as file:
        pickle.dump(ratings_cache, file)
    print("Ratings cache saved.")
    shutil.move("cache/rating_cache_tmp.lzma", "cache/rating_cache.lzma")


def setup(bot):
    global bot_instance
    bot_instance = bot
    bot.add_listener(on_message)
