from datetime import datetime
import json
import discord
from views import *
import API.ratings_cache as ratings_cache
from API.rym_search import search_rym_release
from events import get_user_info

def setup(bot):
    @bot.command(name='randomrating')
    async def randomrating(ctx):
        async with ctx.channel.typing():
            await get_random_rating(ctx)

    @bot.command(name='rdr')
    async def rdr(ctx):
        async with ctx.channel.typing():
            await get_random_rating(ctx)

async def get_random_rating(ctx):
    random_rating = ratings_cache.get_random_rating_from_cache()
    if random_rating:
        user_id = random_rating[0]
        artist_name = random_rating[1]
        release_name = random_rating[2]
        release_year = random_rating[3]
        rating_value = random_rating[4]
        review = random_rating[7]
        search_result = search_rym_release(f"{artist_name} - {release_name}")
        link = None
        album_cover_url = None

        if search_result:
            link = search_result['link']
            if search_result['album_cover_url']:
                album_cover_url = search_result['album_cover_url']
            else:
                album_cover_url = search_result['rym_cover_url']

        user_info = await get_user_info(int(user_id))
        if user_info:
            username, avatar_url = user_info
            star_rating = "<:star:1338267791639445564>" * int(rating_value) + "<:half:1338267704959828069> "  * (1 if rating_value != int(rating_value) else 0)
            embed_title = f"{artist_name} - {release_name} ({release_year})"
            embed_description = f"\n{star_rating}"
            embed_color = discord.Color.blue()
            if float(rating_value) < 2.50:
                embed_color = discord.Color.red()
            if release_year != "Unknown Year" and int(release_year) == datetime.now().year:
                embed_color = discord.Color.green()

            embeds = list()
            embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
            rym_username = get_rym_username(user_id)
            if rym_username:
                embed.set_author(name=f"{username} rated...", url=f"https://rateyourmusic.com/~{rym_username}", icon_url=avatar_url)
            else:
                embed.set_author(name=f"{username} rated...", icon_url=avatar_url)
                
            if album_cover_url:
                embed.set_thumbnail(url=album_cover_url)
            embeds.append(embed)

            sent_message = await ctx.message.channel.send(embed=embeds[0])
            view = Paginator(embeds)
            await sent_message.edit(view=view)
    else:
        await ctx.message.channel.send("No ratings found")

def get_rym_username(user_id):
    with open('cache/rym-cache.json', 'r') as f:
        data = json.load(f)
        rym_username = data.get(str(user_id))
        if rym_username:
            return rym_username
        else:
            return None