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
                raw_cache = pickle.load(file)
                # Convert all keys to integers
                ratings_cache = {int(key): value for key, value in raw_cache.items()}
            except:
                ratings_cache = dict()
    except FileNotFoundError:
        with lzma.open('cache/ratings_cache.lzma', 'wb') as file:
            pickle.dump(dict(), file)

load()

def get_random_rating():
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
    rating_details = {
                'user_id': random_user_id,
                'artist_name': getattr(random_rating, 'artist_name'),
                'title': getattr(random_rating, 'title'),
                'release_year': getattr(random_rating, 'release_year'),
                'rating': getattr(random_rating, 'rating'),
                'ownership': getattr(random_rating, 'ownership'),
                'media_type': getattr(random_rating, 'media_type'),
                'review': getattr(random_rating, 'review'),
                'url': getattr(random_rating, 'url'),
                'release': getattr(random_rating, 'release')
            }
    
    return rating_details

def get_rating_by_number_or_user_id(user_id, number=None):
    user_id = int(user_id) 
    if number is None:
        if user_id in ratings_cache:
            user_ratings = ratings_cache[user_id]
            
            if not user_ratings:
                return {'error': 'No ratings found for this user 🤓'}
            
            # Filter out ratings with a rating of 0.0
            valid_ratings = [rating for rating in user_ratings if getattr(rating, 'rating', 0.0) != 0.0]
            
            if not valid_ratings:
                return {'error': 'No valid ratings found for this user 🤓'}
            
            # Select a random valid rating
            random_rating = random.choice(valid_ratings)
            
            # Format the random rating into a readable string
            rating_details = {
                'user_id': user_id,
                'artist_name': getattr(random_rating, 'artist_name'),
                'title': getattr(random_rating, 'title'),
                'release_year': getattr(random_rating, 'release_year'),
                'rating': getattr(random_rating, 'rating'),
                'ownership': getattr(random_rating, 'ownership'),
                'media_type': getattr(random_rating, 'media_type'),
                'review': getattr(random_rating, 'review'),
                'url': getattr(random_rating, 'url'),
                'release': getattr(random_rating, 'release')
            }
            return rating_details
        else:
            return {'error': 'User not found 🤓'}
    else:
        number = int(number) 
        # Handle the case where a specific rating number is provided
        if user_id in ratings_cache:
            user_ratings = ratings_cache[user_id]
            
            if not user_ratings or number <= 0 or number > len(user_ratings):
                return {'error': 'Invalid rating number 🤓'}
            
            # Get the specific rating by number
            specific_rating = user_ratings[number - 1]
            rating_details = {
                'user_id': user_id,
                'artist_name': getattr(specific_rating, 'artist_name'),
                'title': getattr(specific_rating, 'title'),
                'release_year': getattr(specific_rating, 'release_year'),
                'rating': getattr(specific_rating, 'rating'),
                'ownership': getattr(specific_rating, 'ownership'),
                'media_type': getattr(specific_rating, 'media_type'),
                'review': getattr(specific_rating, 'review'),
                'url': getattr(specific_rating, 'url'),
                'release': getattr(specific_rating, 'release')
            }
            return rating_details
        else:
            return {'error': 'User not found in cache 🤓'}

def get_rating_by_action(action, user=None):
    all_ratings = []
    for user_id, user_ratings in ratings_cache.items():
        for rating in user_ratings:
            all_ratings.append((user_id, rating))

    if not all_ratings:
        return {'error': "No ratings found 🤓"}

    if action == 'roast':
        valid_ratings = [rating for rating in all_ratings if rating[1].rating < 2.5]
    elif action == 'glaze':
        valid_ratings = [rating for rating in all_ratings if rating[1].rating > 4.0]
    else:
        return {'error': "You should teach me what type of action is that one day 🤔"}

    if user:
        user = str(user)
        user_ratings = [rating for rating in all_ratings if str(rating[0]) == user]

        if not user_ratings:
            return {'error': "User not found in the ratings file :O"}

        valid_ratings = [rating for rating in valid_ratings if str(rating[0]) == user]

    if not valid_ratings:
        return {'error': "No valid ratings found 🤓"}

    random_user_id, random_rating = random.choice(valid_ratings)

    rating_details = {
                'user_id': random_user_id,
                'artist_name': getattr(random_rating, 'artist_name'),
                'title': getattr(random_rating, 'title'),
                'release_year': getattr(random_rating, 'release_year'),
                'rating': getattr(random_rating, 'rating'),
                'ownership': getattr(random_rating, 'ownership'),
                'media_type': getattr(random_rating, 'media_type'),
                'review': getattr(random_rating, 'review'),
                'url': getattr(random_rating, 'url'),
                'release': getattr(random_rating, 'release')
            }

    return rating_details

def save():
    with lzma.open('cache/ratings_cache_tmp.lzma', 'wb') as file:
        pickle.dump(ratings_cache, file)
    print("Ratings cache saved.")
    shutil.move("cache/ratings_cache_tmp.lzma", "cache/ratings_cache.lzma")