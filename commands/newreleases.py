import json
import os
import requests
import time
from datetime import datetime
from views import *
from bs4 import BeautifulSoup
from API.rym_search import search_rym_release
import discord


def setup(bot):
    @bot.command(name='new', aliases=['newreleases'])
    async def newreleases(ctx):
        async with ctx.channel.typing():
            await get_new_releases(ctx)


def check_new_releases_cache(artist_name, release_name):
    file_path = "cache/new_releases.json"

    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump([], file)

    with open(file_path, 'r') as file:
        shown_albums = json.load(file)

    album_identifier = f"{artist_name} - {release_name}"
    if album_identifier in shown_albums:
        return True

    shown_albums.append(album_identifier)
    with open(file_path, 'w') as file:
        json.dump(shown_albums, file, indent=4) 

    return False


async def get_new_releases(ctx):
    url = "https://www.sputnikmusic.com/newreleases.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    releases_number = 0

    try:
        with requests.Session() as session:
            response = session.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                sputnik = soup.find("table", class_="plaincontentbox")
                general_table = sputnik.find("tr")
                # Get the release month (can be useful in the future)
                month = general_table.find("font", color="#555555").get_text(strip=True)
                releases_table = general_table.findAll("td", class_="hi")
                
                for release in releases_table:
                    artist_data = release.find("font", color="#111111")
                    album_data = release.find("font", color="#555555")

                    if artist_data and album_data:
                        artist_name = artist_data.find("b").get_text(strip=True)
                        release_name = album_data.get_text(strip=True)

                        # Skip if album was already shown
                        if check_new_releases_cache(artist_name, release_name):
                            continue
                        
                        releases_number += 1
                        rym_data = search_rym_release(f"{artist_name} - {release_name}")
                        embed_color = discord.Color.green()

                        if rym_data and rym_data.get('artist_name'):
                            artist_name = rym_data['artist_name']
                            release_name = rym_data['release_name']
                            release_year = rym_data['release_year']
                            genres = rym_data['genres']
                            rating_value = rym_data['rating_value']
                            formatted_rating_count = rym_data['formatted_rating_count']
                            performers = rym_data['performers']

                            if rym_data.get('album_cover_url'):
                                album_cover_url = rym_data.get('album_cover_url')
                            elif rym_data.get('rym_cover_url'):
                                album_cover_url = rym_data.get('rym_cover_url')
                            else:
                                album_cover_url = None

                            album_wiki = rym_data['album_wiki']
                            streaming_links = rym_data['streaming_links']
                            link = rym_data['link']
                            likes = len(rym_data.get('liked_users', []))
                            dislikes = len(rym_data.get('disliked_users', []))

                            embed_title = f"{artist_name} - {release_name} ({release_year})"
                            if rating_value == "No Rating" or formatted_rating_count == "No Ratings":
                                embed_description = ""
                            else:    
                                embed_description = f"*{genres}*\n\n**{rating_value}** ⭐ from **{formatted_rating_count}** ratings"

                            embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
                            if album_cover_url:
                                embed.set_thumbnail(url=album_cover_url)

                            embed.set_footer(text=f"Source: Sputnikmusic")
                            sent_message = await ctx.channel.send(embed=embed)
                    
                            view = RYMViewReleases(album_wiki, embed, likes=likes, dislikes=dislikes, original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name, streaming_links=streaming_links, performers=performers)
                            view.link = link

                            await sent_message.edit(view=view)
                        else:
                            embed_title = f"{artist_name} - {release_name} ({datetime.now().year})"
                            link = f"https://rateyourmusic.com/search?searchtype=a&searchterm={artist_name.replace(' ', '+')}+{release_name.replace(' ', '+')}&searchtype="
                            embed = discord.Embed(title=embed_title, url=link, color=embed_color)

                            embed.set_footer(text=f"Source: Sputnikmusic")
                            sent_message = await ctx.channel.send(embed=embed)
                    
                            view = RYMViewReleases(original_message_id=sent_message.id, artist_name=artist_name, release_name=release_name)

                            await sent_message.edit(view=view)

                        time.sleep(5) # Rate limit
            else:
                await print(f"Failed to fetch the webpage. HTTP Status Code: {response.status_code}")
    except Exception as e:
        await print(f"An error occurred: {e}")
