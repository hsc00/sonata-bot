import logging
import discord
from discord.ui import View, Button
import json
from discord.ext import commands
from googlesearch import search
import os
from archived.album_info import AlbumMethods
from emoji_links import streaming_emojis

# Initialize the AlbumMethods client
album_client = AlbumMethods()

# Create cache folder if it doesn't exist
if not os.path.exists('cache'):
    os.makedirs('cache')

# Load cache from file
cache_file = 'cache/album-cache.json'
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cache = json.load(f)
else:
    cache = {}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_aoty_link(album_name):
    query = f"{album_name} site:albumoftheyear.org"
    try:
        for result in search(query, num_results=20):
            if "albumoftheyear.org/album/" in result and "review" not in result and "user-reviews" not in result and "comments" not in result:
                return result
    except Exception as e:
        logging.error(f"Error during Google search: {e}")
    logging.warning('No AOTY link found')
    return None

async def fetch_album_details(album_id):
    album_details = album_client.album_details(album_id)
    logging.info(f'Fetched album details: {album_details}')
    return album_details

async def send_album_details(ctx, album_details, album_id):
    try:
        album_cover_url = album_details['cover_url']
        release_year = album_details['release_date'].split()[-1]

        embed = discord.Embed(title=f"{album_details['artist_name']} - {album_details['album_title']} ({release_year})", url=f"https://www.albumoftheyear.org/album/{album_id}")
        embed.set_thumbnail(url=album_cover_url)
        embed.add_field(name="User Score", value=album_details['user_score'], inline=True)
        embed.add_field(name="Number of Ratings", value=album_details['num_ratings'], inline=True)
        embed.add_field(name="Rank of the Year", value=album_details['rank_of_year'], inline=True)
        embed.add_field(name="All-time Rank", value=album_details['alltime_rank'], inline=True)
        embed.add_field(name="Critic Score", value=album_details['critic_score'], inline=True)
        embed.add_field(name="Genres", value=album_details['genre'], inline=False)

        # Create the view and add buttons with custom emojis
        view = View()
        for link in album_details['streaming_links']:
            service_name = link["name"]
            emoji = streaming_emojis.get(service_name, None)
            if emoji:
                button = Button(
                    url=link["url"], 
                    style=discord.ButtonStyle.link,
                    emoji=emoji
                )
            else:
                button = Button(
                    label=service_name, 
                    url=link["url"], 
                    style=discord.ButtonStyle.link
                )
            view.add_item(button)

        # Send the message with the embed and view
        await ctx.send(embed=embed, view=view)
        logging.info(f'Sent album details: {album_details["album_title"]}')
    except KeyError as e:
        logging.error(f'Missing key in album details: {e}')
        await ctx.send('Error: Missing key in album details.')
    except Exception as e:
        logging.error(f'Error sending album details: {e}')
        await ctx.send('Error: Could not send album details.')

def setup(bot):
    @bot.command(name='album', aliases=['ab'])
    @commands.cooldown(1, 5, commands.BucketType.user)  # Add cooldown
    async def album(ctx, *album_name: str):
        original_album_name = " ".join(album_name).strip().lower()
        album_name_no_spaces = "".join(album_name).strip().lower()
        logging.info(f'Received album command: {original_album_name}')

        # Check cache first
        if album_name_no_spaces in cache:
            album_details = cache[album_name_no_spaces]
            album_details['request_count'] += 1
            logging.info(f'Cache hit for album: {original_album_name}')

            # Save the updated cache to file
            with open(cache_file, 'w') as f:
                json.dump(cache, f)

            # Refresh album details after 5 requests
            if album_details['request_count'] > 5:
                aoty_link = get_aoty_link(original_album_name)
                if aoty_link:
                    album_id = aoty_link.split('/')[-1].split('-')[0]
                    try:
                        album_details = await fetch_album_details(album_id)
                        album_details['request_count'] = 1  # Reset request count to 1
                        cache[album_name_no_spaces] = album_details
                        with open(cache_file, 'w') as f:
                            json.dump(cache, f)
                        await send_album_details(ctx, album_details, album_id)
                    except Exception as e:
                        logging.error(f'Error fetching album details: {e}')
                        await ctx.send('Error: Could not fetch album details.')
                else:
                    await ctx.send('Release not found. Try again')
                    logging.warning('Could not find AOTY link')
            else:
                await send_album_details(ctx, album_details, album_name_no_spaces)
        else:
            logging.info(f'Cache miss for album: {original_album_name}')
            aoty_link = get_aoty_link(original_album_name)
            if aoty_link:
                album_id = aoty_link.split('/')[-1].split('-')[0]
                try:
                    album_details = await fetch_album_details(album_id)
                    album_details['request_count'] = 1  # Initialize request count to 1
                    cache[album_name_no_spaces] = album_details
                    with open(cache_file, 'w') as f:
                        json.dump(cache, f)
                    await send_album_details(ctx, album_details, album_id)
                except Exception as e:
                    logging.error(f'Error fetching album details: {e}')
                    await ctx.send('Error: Could not fetch album details.')
            else:
                await ctx.send('Release not found. Try again')
                logging.warning('Could not find AOTY link')

        # Log the username and query
        logging.info(f'{ctx.author} searched {original_album_name}')

    @album.error
    async def album_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Error: Missing required argument `album_name`. Please provide the album name.')
            logging.error('Missing required argument `album_name`')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'{int(error.retry_after)} seconds cooldown')
