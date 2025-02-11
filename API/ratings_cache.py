import lzma
import pickle
import shutil
import random

global ratings_cache
ratings_cache = dict()

def load():
    global ratings_cache
    try:
        with lzma.open('cache/ratings_cache.lzma', 'rb') as file:
            try:
                ratings_cache = pickle.load(file)
            except:
                ratings_cache = dict()
    except FileNotFoundError:
        with lzma.open('cache/ratings_cache.lzma', 'wb') as file:
            pickle.dump(dict(), file)


def get_random_rating_from_cache():
    all_ratings = []
    # Collect all ratings from the cache along with the user ID
    for user_id, user_ratings in ratings_cache.items():
        for rating in user_ratings:
            all_ratings.append((user_id, rating))

    # Check if there are any ratings
    if not all_ratings:
        return "No ratings found."

    valid_ratings = [rating for rating in all_ratings if rating[1].rating != 0.0]

    # Select a random valid rating
    random_user_id, random_rating = random.choice(valid_ratings)

    # Format the random rating into a readable string
    rating_details = (
        random_user_id,
        random_rating.artist_name, 
        random_rating.title, 
        random_rating.release_year, 
        random_rating.rating,
        random_rating.ownership,
        random_rating.media_type,
        random_rating.review,
        random_rating.url,
        random_rating.release
    )
    return rating_details


def save():
    with lzma.open('cache/ratings_cache_tmp.lzma', 'wb') as file:
        pickle.dump(ratings_cache, file)
    print("Ratings cache saved.")
    shutil.move("cache/ratings_cache_tmp.lzma", "cache/ratings_cache.lzma")