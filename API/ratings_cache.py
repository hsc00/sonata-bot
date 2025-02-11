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


def get_random_rating():
    all_ratings = []
    # Collect all ratings from the cache
    for user in ratings_cache:
        all_ratings.extend(ratings_cache)
        return all_ratings
    else:
        return None

def save():
    with lzma.open('cache/ratings_cache_tmp.lzma', 'wb') as file:
        pickle.dump(ratings_cache, file)
    print("Ratings cache saved.")
    shutil.move("cache/ratings_cache_tmp.lzma", "cache/ratings_cache.lzma")