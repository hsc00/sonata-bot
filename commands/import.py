import csv
import requests
from API.rympy_rating import Rating
import API.ratings_cache as ratings_cache
import API.album_cache as album_cache
import API.artist_cache as artist_cache

def setup(bot):
    @bot.command(name='import')
    async def import_ratings(ctx):
        async with ctx.channel.typing():
            await process_ratings_command(ctx.message)

    @bot.command(name='i')
    async def i(ctx):
        async with ctx.channel.typing():
            await process_ratings_command(ctx.message)


def import_ratings(url,user_id):
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

        def update_cache(rating, user_id, rating_type):
            key_album = artist_cache.normalize_name(rating.artist_name) + "-" + album_cache.normalize_name(rating.title)
            key_artist = artist_cache.normalize_name(rating.artist_name)
            album_cache_json = album_cache.load_cache()
            artist_cache_json = artist_cache.load_cache()
            album_data = album_cache_json.setdefault(key_album, {})
            artist_data = artist_cache_json.setdefault(key_artist, {})

            if user_id not in album_data.setdefault(rating_type, []):
                album_data[rating_type].append(user_id)
            if user_id not in artist_data.setdefault(rating_type, []):
                artist_data[rating_type].append(user_id)

            album_cache.save_cache(album_cache_json)
            artist_cache.save_cache(artist_cache_json)

        if rating.rating > 4:
            update_cache(rating, user_id, "liked_users")
        elif rating.rating < 2 and rating.rating > 0:
            update_cache(rating, user_id, "disliked_users")


    return ratings_list
            

async def process_ratings_command(message):
    user_id = message.author.id
    if message.attachments:
        await message.reply("I'll try to import your ratings!")
        ratings_cache.ratings_cache[user_id] = import_ratings(message.attachments[0].url, user_id)
    else:
        await message.reply("I can't import as there is no attachment with your ratings in your message")
        return

    await message.reply("Your ratings have been imported successfully.")
    ratings_cache.save()