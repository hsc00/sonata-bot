from datetime import datetime
import re
import discord
from API.search_lastfm import get_lastfm_track
from API.rym_search import search_rym_release
from views import Paginator
from API.ratings_cache import ratings_cache

def setup(bot):
    @bot.command(name='whoknowsalbum')
    async def whoknowsalbum(ctx):
        async with ctx.channel.typing():
            await process_release_link_or_text(ctx)

    @bot.command(name='wa')
    async def wa(ctx):
        async with ctx.channel.typing():
            await process_release_link_or_text(ctx)

async def process_release_link_or_text(ctx):
    message = ctx.message
    release_query = get_release_query(message)
    
    if not release_query:
        await message.channel.reply('Please provide an album or use `!setfm` to set your last.fm account.')
        return

    search_result = search_rym_release(release_query)
    if not search_result:
        await message.channel.send(f'**{release_query}** not found.')
        return

    _, embeds = build_embed(ctx, search_result)

    if embeds:
        sent_message = await message.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(view=view)
    else:
        await message.channel.send(f'No ratings found for **{release_query.title()}**.')

def get_release_query(message):
    content_parts = message.content.split(' ', 1)
    return content_parts[1] if len(content_parts) > 1 else get_lastfm_track(message.author.id, 'release')

def build_embed(ctx, search_result):
    artist_name = search_result['artist_name']
    release_name = search_result['release_name']
    release_year = search_result['release_year']
    genres = search_result['genres']
    rating_value = search_result['rating_value']
    formatted_rating_count = search_result['formatted_rating_count']
    best_album_position = search_result['best_album_position']
    all_time_album_position = search_result['all_time_album_position']
    if search_result.get('album_cover_url'):
        album_cover_url = search_result['album_cover_url']
    else:
        album_cover_url = search_result['rym_cover_url']
    link = search_result['link']

    embed_title = f"{artist_name} - {release_name} ({release_year})"
    if rating_value != "No Rating" or formatted_rating_count != "No Ratings":
        embed_description = f"*{genres}*\n\n**{rating_value}** ⭐ from **{formatted_rating_count}** ratings"
    else:
        embed_description = ""
    embed_color = determine_embed_color(rating_value, release_year)

    if best_album_position:
        best_album_number = extract_album_number(best_album_position)
        embed_description += f"\n#**{best_album_number}** of [{release_year}](https://rateyourmusic.com/charts/top/album/{release_year}/)"

    if all_time_album_position:
        all_time_album_number = extract_album_number(all_time_album_position)
        embed_description += f", #**{all_time_album_number}** [overall](https://rateyourmusic.com/charts/top/album/all-time/)"
        embed_color = determine_all_time_color(embed_color, all_time_album_number)

    average, ratings_count, embeds, user_ratings = (0, 0), 0, [], []

    for user, ratings in ratings_cache.items():
        for rating in ratings:
            if (rating.artist_name in artist_name or rating.artist_name_localized in artist_name) and rating.title in release_name and rating.release_year == int(release_year) and rating.rating:
                average, user_ratings, ratings_count = send_ratings(ctx, user, rating, average, user_ratings, ratings_count)
    
        if ratings_count > 10:
            # Split user_ratings into chunks of 10 entries
            paginated_ratings = [user_ratings[i:i+10] for i in range(0, len(user_ratings), 10)]
            for rating_pages in paginated_ratings:
                embed_content = "".join(rating_pages)  # Combine the list into a single string
                embeds.append(create_embed(ctx, embed_title, paginated_ratings, embed_description, embed_content, average, link, embed_color, album_cover_url, ctx.author.name))
            user_ratings, ratings_count, average = [], 0, (0, 0)
    
    if ratings_count:
        # Handle remaining ratings
        embed_content = "".join(user_ratings)
        embeds.append(create_embed(ctx, embed_title, None, embed_description, embed_content, average, link, embed_color, album_cover_url, ctx.author.name))

    return None, embeds

def determine_embed_color(rating_value, release_year):
    embed_color = discord.Color.blue()
    if rating_value != "No Rating":
        if float(rating_value) < 2.50:
            embed_color = discord.Color.red()
    if release_year != "Unknown Year" and int(release_year) == datetime.now().year:
        embed_color = discord.Color.green()
    return embed_color

def determine_all_time_color(embed_color, all_time_album_number):
    if all_time_album_number <= 250:
        return discord.Color.gold()
    if all_time_album_number <= 1000:
        return discord.Color.from_rgb(214, 214, 214)
    if all_time_album_number > 1000:
        return discord.Color.from_rgb(151, 117, 71)
    return embed_color

def extract_album_number(position):
    if not position.isdigit():
        match = re.search(r'#(\d+)', position)
        return int(match.group(1)) if match else None
    return int(position)

def send_ratings(ctx, user, rating, average, user_ratings, ratings_count):
    average = (average[0] + rating.rating, average[1] + 1)
    star_rating = f"{rating.rating}"
    if ctx.author.id == int(user):
        rating_entry = f"**<@{user}> • {star_rating}** ⭐"
    else:
        rating_entry = f"<@{user}> • **{star_rating}** ⭐"
    rating_entry += "\n"
    user_ratings.append(rating_entry)  # Add the rating entry to the list
    ratings_count += 1
    return average, user_ratings, ratings_count


def create_embed(ctx, embed_title, paginated_ratings, embed_description, user_ratings, average, link, embed_color, album_cover_url, author_name):
    if average[1]:
        average = average[0] / average[1]
        embed_description += f"\n\n{ctx.guild.name} Rating: **{round(average, 2)}** ⭐\n\n{user_ratings}"
    embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
    if album_cover_url:
        embed.set_thumbnail(url=album_cover_url)
    if paginated_ratings:
        embed.set_footer(text=f"Requested by {author_name} • Page {len(paginated_ratings)}")
    else:
        embed.set_footer(text=f"Requested by {author_name}")
    return embed
