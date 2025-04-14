from datetime import datetime
import html
import re
import discord
import urllib
from API.search_lastfm import get_lastfm_track
from API.rym_search import search_rym_artist
from utils.text_formatters import *
from views import Paginator
from API.ratings_cache import ratings_cache

def setup(bot):
    @bot.command(name='artistratings', aliases=['ar'])
    async def artist_ratings(ctx):
        async with ctx.channel.typing():
            await get_artist_ratings(ctx)

async def get_artist_ratings(ctx):
    message = ctx.message
    release_query = get_release_query(message)

    artist_name, user_id = get_user_id(release_query)
    user_id = int(ctx.author.id) if user_id is None else int(user_id)

    if not artist_name:
        await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
        return

    search_result = search_rym_artist(artist_name)
    if not search_result:
        await message.channel.send(f'**{artist_name.title()}** not found.')
        return

    _, embeds = build_embed(ctx, search_result, user_id)

    if embeds:
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(view=view)
    else:
        await message.channel.send(f'No ratings found for **{release_query.title()}**.')

def get_release_query(message):
    content_parts = message.content.split(' ', 1)
    return content_parts[1] if len(content_parts) > 1 else get_lastfm_track(message.author.id, 'artist')

def build_embed(ctx, search_result, user_id):
    artist_name = search_result['artist_name']
    genres = search_result['genres']

    if search_result.get('artist_img_url'):
        artist_img_url = search_result['artist_img_url']
    else:
        artist_img_url = search_result['rym_img_url']
    link = search_result['link']

    embed_description = f"*{genres}*"
    embed_title = artist_name
    embed_color = discord.Color.blue()

    average, ratings_count, embeds, user_ratings = (0, 0), 0, [], []  # Initialize user_ratings as a list

    for user, ratings in ratings_cache.items():
        if user == int(user_id):
            # Sort by higher rating
            sorted_ratings = sorted(ratings, key=lambda x: x.rating, reverse=True)
            
            for rating in sorted_ratings:
                if (artist_name in rating.artist_name or artist_name in rating.artist_name_localized) and rating.rating != 0.0:
                    average, user_ratings, ratings_count = send_rating(rating, average, user_ratings, ratings_count)

            if ratings_count > 10:
                # Split user_ratings into pages of 10 releases
                paginated_ratings = [user_ratings[i:i+10] for i in range(0, len(user_ratings), 10)]
                for ratings_page in paginated_ratings:
                    user_ratings = "".join(ratings_page)
                    embeds.append(create_embed(user_id, paginated_ratings, embed_title, embed_description, user_ratings, average, link, embed_color, artist_img_url, ctx.author.name))
                user_ratings, ratings_count, average = [], 0, (0, 0)  # Reset user_ratings as a list

    if ratings_count:
        user_ratings = "".join(user_ratings)
        embeds.append(create_embed(user_id, None, embed_title, embed_description, user_ratings, average, link, embed_color, artist_img_url, ctx.author.name))

    return None, embeds


def send_rating(rating, average, user_ratings, ratings_count):
    rating_entry = ""
    average = (average[0] + rating.rating, average[1] + 1)

    star_rating = "📝" if rating.rating == "0" else "<:star:1338267791639445564>" * int(rating.rating) + "<:half:1338267704959828069> " * (1 if rating.rating != int(rating.rating) else 0)
    rating_entry += f"**[{add_newline_limit(html.unescape(rating.title))}](https://rateyourmusic.com/search?searchtype=a&searchterm={urllib.parse.quote(rating.title)}&searchtype=)** • {star_rating}\n"

    user_ratings.append(rating_entry)  # Append the rating_entry string to the list
    ratings_count += 1

    return average, user_ratings, ratings_count


def create_embed(user_id, paginated_ratings, embed_title, embed_description, user_ratings, average, link, embed_color, artist_img_url, author_name):
    if average[1]:
        average = average[0] / average[1]
        embed_description += f"\n\n<@{user_id}>\n Average Rating: **{round(average, 2)}** ⭐\n\n{user_ratings}"
    embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
    if artist_img_url:
        embed.set_thumbnail(url=artist_img_url)
    if paginated_ratings:
        embed.set_footer(text=f"Requested by {author_name} • Page 1/{len(paginated_ratings)}")
    else:
        embed.set_footer(text=f"Requested by {author_name}")
    return embed
