import csv
import logging
import lzma
import pickle
import shutil
import discord
import requests
from views import *
import time
from datetime import datetime
import re
from API.rym_search import search_rym_release, search_rym_artist
from API.rympy_rating import *
from API.setlist_search import get_setlist

global ratings_cache
ratings_cache = dict()
bot_instance = None
google_tokens = None
cse_id = None
cse_id_streaming = None
lastfm_api_key = None
setlist_api_key = None

try:
    with lzma.open('cache/ratings_cache.lzma', 'rb') as file:
        try:
            ratings_cache = pickle.load(file)
        except:
            ratings_cache = dict()
except FileNotFoundError:
    with lzma.open('cache/ratings_cache.lzma', 'wb') as file:
        pickle.dump(dict(), file)

async def on_ready():
    logging.info(f'Logged in as {bot_instance.user}')
        
async def on_message(message):
    if message.author == bot_instance.user:
        return
    if 'rateyourmusic.com/release/' in message.content or message.content.startswith('!album') or message.content.startswith('!ab'):
        async with message.channel.typing():
            await process_release_link_or_text(message)
        time.sleep(5)
    elif 'rateyourmusic.com/artist/' in message.content or message.content.startswith('!artist') or message.content.startswith('!a'):
        async with message.channel.typing():
            await process_artist_link_or_text(message)
            time.sleep(5)
    elif message.content.startswith('!import') or message.content.startswith('!i'):
        await process_ratings_command(message)
    elif message.content.startswith('!setlist') or message.content.startswith('!st'):
        async with message.channel.typing():
            await process_setlist(message)
            time.sleep(5)
    elif message.content.startswith('!wa'):
        #await process_who_knows_command(message)
        pass

async def process_artist_link_or_text(message):
    artist_query = message.content
    if artist_query.startswith('!artist') or artist_query.startswith('!a'):
        content_parts = message.content.split(' ', 1)
        if len(content_parts) < 2:
            await message.channel.send('Please provide an artist.')
            return
        artist_query = artist_query.split(' ', 1)[1] 
        
        artist_info = search_rym_artist(artist_query, google_tokens, cse_id, cse_id_streaming, lastfm_api_key)
    else:
        #clean message link
        match = re.search(r'(https?://)?(www\.)?rateyourmusic.com/.+', artist_query)
        artist_query = match.group(0)

        # Check if the query is a valid RYM link
        if artist_query.startswith('https://rateyourmusic.com/artist/') and len(artist_query.split('/')) > 3:
            artist_info = search_rym_artist(artist_query, google_tokens, cse_id, cse_id_streaming, lastfm_api_key)
        elif artist_query.startswith('rateyourmusic.com/'):
            await message.channel.send('Invalid link. Please provide a valid RateYourMusic **artist** link.')
            return
        
    if artist_info:
        artist_name = artist_info['artist_name']
        if artist_info['founded_year'] == "Unknown":
            founded_year = ""
        else:
            founded_year = artist_info['founded_year']

        genres = artist_info['genres']
        listeners = artist_info['listeners']
        similar_artists = artist_info['similar_artists']
        if artist_info['artist_img_url']:
            artist_img_url = artist_info['artist_img_url']
        else:
            artist_img_url = artist_info['rym_img_url']

        artist_summary = artist_info['summary']
        streaming_links = artist_info['streaming_links']
        link = artist_info['link']
        likes = len(artist_info.get('liked_users', []))
        dislikes = len(artist_info.get('disliked_users', []))


        embed_title = f"{artist_name}"
        embed_description = f"*{genres}*\n\nListeners: **{listeners}**\n {founded_year}\n\n {artist_summary}"

        embed = discord.Embed(title=embed_title, description=embed_description, url=link)
        if artist_img_url:
            embed.set_thumbnail(url=artist_img_url)

        embed.set_footer(text=f"Requested by {message.author.display_name}")
        sent_message = await message.channel.send(embed=embed)

        view = RYMViewArtists(artist_name, similar_artists, embed, likes=likes, dislikes=dislikes, original_message_id=sent_message.id, streaming_links=streaming_links, release_name=None)
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

# searches release on rym
async def process_release_link_or_text(message):
    if message.content.startswith('!album') or message.content.startswith('!ab'):
        content_parts = message.content.split(' ', 1)
        if len(content_parts) > 1:
            query = content_parts[1]
        else:
            await message.channel.send('Please provide a release.')
            return
    else:
        #clean message link
        match = re.search(r'(https?://)?(www\.)?rateyourmusic.com/.+', message.content)
        query = match.group(0)

   # Check if the query is a valid RYM link
    if (query.startswith('https://rateyourmusic.com/release/')) and len(query.split('/')) > 5:
        search_result = search_rym_release(query, google_tokens, cse_id, cse_id_streaming, lastfm_api_key)
    elif query.startswith('https://rateyourmusic.com/'):
        await message.channel.send('Invalid link. Please provide a valid RateYourMusic **release** link.')
        return
    else:
        # Perform a Google search if it's plain text
        search_result = search_rym_release(query, google_tokens, cse_id, cse_id_streaming, lastfm_api_key)
        if not search_result or not search_result['link'].startswith('https://rateyourmusic.com/release/'):
            await message.channel.send('Please provide a valid RateYourMusic **release** name.')
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
        album_cover_url = search_result['album_cover_url']
        album_wiki = search_result['album_wiki']
        streaming_links = search_result['streaming_links']
        link = search_result['link']
        likes = len(search_result.get('liked_users', []))
        dislikes = len(search_result.get('disliked_users', []))


        embed_title = f"{artist_name} - {release_name} ({release_year})"
        embed_description = f"*{genres}*\n\n**{rating_value}** ⭐ from **{formatted_rating_count}** ratings"
        embed_color = discord.Color.blue()

        if best_album_position:
            best_album_number = int(re.search(r'#(\d+)', best_album_position).group(1))
            embed_description += f"\n#**{best_album_number}** of {release_year}"
        if all_time_album_position:
            all_time_album_number = int(re.search(r'#(\d+)', all_time_album_position).group(1))
            embed_description += f", #**{all_time_album_number}** overall"
            embed_color = (
                discord.Color.gold() if all_time_album_number <= 250 else
                discord.Color.from_rgb(214, 214, 214) if all_time_album_number <= 1000 else
                discord.Color.from_rgb(151, 117, 71) if all_time_album_number > 1000 else
                embed_color
            )
        if float(rating_value) < 2.50:
            embed_color = discord.Color.red()
        if release_year !="Unknown Year":
            if int(release_year) == datetime.now().year:
                embed_color = discord.Color.green()


        embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
        if album_cover_url:
            embed.set_thumbnail(url=album_cover_url)

        embed.set_footer(text=f"Requested by {message.author.display_name}")
        sent_message = await message.channel.send(embed=embed)
 
        view = RYMViewReleases(album_wiki, embed, likes=likes, dislikes=dislikes, original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name, streaming_links=streaming_links, performers=performers)
        view.link = link

        await sent_message.edit(view=view)

async def process_setlist(message):
    if message.content.startswith('!setlist') or message.content.startswith('!st'):
        content_parts = message.content.split(' ', 1)
        if len(content_parts) > 1:
            query = content_parts[1]
            setlist = get_setlist(query, setlist_api_key)
        else:
            await message.channel.send('Please provide a valid artist.')
            return

        if 'url' in setlist:
            link = setlist['url']
            concert_name = setlist['concert_name']
            city_name = setlist['city_name']
            country_name = setlist['country_name']
            concert_date = setlist['concert_date']
            tracks_played = setlist['tracks_played']

            if not tracks_played:
                await message.channel.send(f'No tracks found in the setlist. You can be the one adding them [here]({link})')
                return
            
            pages = [tracks_played[i:i + 10] for i in range(0, len(tracks_played), 10)]    

            embed_title = f"{concert_name}, {city_name}, {country_name}"
            embed_description = f"{concert_date}\n\n"

            embed = discord.Embed(title=embed_title, description=embed_description, url=link)
            embed.set_footer(text=f"Requested by {message.author.display_name}")

            tracks_description = "\n".join(f" - {track}" for track in pages[0])
            embed.description += tracks_description
            
            sent_message = await message.channel.send(embed=embed)
            view = Paginator(pages, embed, link)
            await sent_message.edit(embed=embed, view=view)
        else:
            await message.channel.send('Setlist not found.')

def setup(bot, tokens, cse, cse_streaming, lastfm, setlistfm_api_key):
    global bot_instance, google_tokens, cse_id, cse_id_streaming, lastfm_api_key, setlist_api_key
    bot_instance = bot
    google_tokens = tokens
    cse_id = cse
    cse_id_streaming = cse_streaming
    lastfm_api_key = lastfm
    setlist_api_key = setlistfm_api_key

    bot.add_listener(on_ready)
    bot.add_listener(on_message)
