import logging
import discord
from views import RYMView
import time
from datetime import datetime
import re
from API.rym_search import search_rym, search_rym_artist

bot_instance = None
google_tokens = None
cse_id = None
lastfm_api_key = None

async def on_ready():
    logging.info(f'Logged in as {bot_instance.user}')

async def on_message(message):
    if 'rateyourmusic.com/release/' in message.content or message.content.startswith('!album') or message.content.startswith('!ab'):
        async with message.channel.typing():
            await process_rym_link_or_text(message)
            time.sleep(5)
    elif 'rateyourmusic.com/artist/' in message.content or message.content.startswith('!artist') or message.content.startswith('!a'): 
        async with message.channel.typing(): 
            time.sleep(5)
        
async def on_message(message):
    if 'rateyourmusic.com/release/' in message.content or message.content.startswith('!album') or message.content.startswith('!ab'):
        async with message.channel.typing():
            await process_rym_link_or_text(message)
            time.sleep(5)
    elif 'rateyourmusic.com/artist/' in message.content or message.content.startswith('!artist') or message.content.startswith('!a'):
        async with message.channel.typing():
            await process_artist_link_or_text(message)
            time.sleep(5)

async def process_artist_link_or_text(message):
    artist_query = message.content
    if artist_query.startswith('!artist') or artist_query.startswith('!a'):
        artist_query = artist_query.split(' ', 1)[1] 

    artist_info = search_rym_artist(artist_query, google_tokens, cse_id, lastfm_api_key)
    print(artist_info)

# searches release on rym
async def process_rym_link_or_text(message):
    if message.content.startswith('!album') or message.content.startswith('!ab'):
        content_parts = message.content.split(' ', 1)
        if len(content_parts) > 1:
            query = content_parts[1]
        else:
            await message.channel.send('Please provide a search query or link.')
            return
    else:
        query = message.content

    # Check if the query is a valid RYM link
    if query.startswith('rateyourmusic.com/release/'):
        search_result = search_rym(query, google_tokens, cse_id, lastfm_api_key)
    elif query.startswith('rateyourmusic.com/'):
        await message.channel.send('Invalid link. Please provide a valid RateYourMusic **release** link.')
        return
    else:
        # Perform a Google search if it's plain text
        search_result = search_rym(query, google_tokens, cse_id, lastfm_api_key)
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
        likes = search_result.get('likes', 0)
        dislikes = search_result.get('dislikes', 0)

        embed_title = f"{artist_name} - {release_name} ({release_year})"
        embed_description = f"*{genres}*\n\n**{rating_value}** ⭐ from **{formatted_rating_count}** ratings"
        embed_color = discord.Color.blue()

        if best_album_position:
            best_album_number = int(re.search(r'#(\d+)', best_album_position).group(1))
            embed_description += f"\n**{best_album_number}** of {release_year}"
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

        embed.add_field(name="\u200b", value=f"❤️ {likes} \t 👎 {dislikes}", inline=True)

        embed.set_footer(text=f"Requested by {message.author.display_name}")
        sent_message = await message.channel.send(embed=embed)

        view = RYMView(album_wiki, embed, original_message_id=sent_message.id, release_name=release_name, streaming_links=streaming_links, performers=performers)
        view.link = link

        await sent_message.edit(view=view)

def setup(bot, tokens, cse, lastfm):
    global bot_instance, google_tokens, cse_id, lastfm_api_key
    bot_instance = bot
    google_tokens = tokens
    cse_id = cse
    lastfm_api_key = lastfm

    bot.add_listener(on_ready)
    bot.add_listener(on_message)
