import lzma
import math
import pickle
import shutil
import random
import urllib

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
        valid_ratings = [rating for rating in all_ratings if 0 < rating[1].rating < 2.5]
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

def get_most_rated_releases():
    # Dictionary to hold aggregated release data
    all_ratings = {}

    # Loop through the ratings_cache to aggregate release information
    for user_ratings in ratings_cache.values():  # Only focus on user_ratings
        for rating in user_ratings:
            artist_name = getattr(rating, 'artist_name', None)  # Safely retrieve artist name
            release_name = getattr(rating, 'title', None)  # Retrieve release title
            link = f"https://rateyourmusic.com/search?searchtype=a&searchterm={urllib.parse.quote(artist_name + ' ' + release_name)}&searchtype="

            if release_name and artist_name:
                if release_name not in all_ratings:
                    all_ratings[release_name] = {
                        'artist_name': artist_name,
                        'release_name': release_name,
                        'link': link,
                        'rating_count': 0 
                    }
                
                all_ratings[release_name]['rating_count'] += 1

    if not all_ratings:
        return "No rated releases found."

    # Sort releases by the number of ratings in descending order
    sorted_releases = sorted(all_ratings.values(), key=lambda x: x['rating_count'], reverse=True)

    # Limit the results to the top 100 releases
    top_releases = sorted_releases[:100]

    return top_releases

def get_most_rated_artists():
    all_artists = {}

    for user_ratings in ratings_cache.values():
        for rating in user_ratings:
            artist_name = getattr(rating, 'artist_name', None) 
            link = f"https://rateyourmusic.com/artist/{artist_name.lower().replace(' ', '-')}"

            if artist_name: 
                if artist_name not in all_artists:
                    all_artists[artist_name] = {
                        'artist_name': artist_name,
                        'link': link,
                        'rating_count': 0 
                    }
                
                # Increment the rating count for this artist
                all_artists[artist_name]['rating_count'] += 1

    if not all_artists:
        return "No rated artists found."

    # Sort artists by the number of ratings in descending order
    sorted_artists = sorted(all_artists.values(), key=lambda x: x['rating_count'], reverse=True)

    # Limit the results to the top 100 artists
    top_artists = sorted_artists[:100]

    return top_artists


def get_best_rated_artists(user_id):
    all_artists = {}
    for user, user_ratings in ratings_cache.items():
        if user_id is not None and user != int(user_id):
            continue
        for rating in user_ratings:
            artist_name = getattr(rating, 'artist_name', None)
            album_rating = getattr(rating, 'rating', None)
            release_title = getattr(rating, 'title', None) 
            if artist_name == "Various Artists":
                continue
            link = f"https://rateyourmusic.com/artist/{artist_name.lower().replace(' ', '-')}"

            if artist_name and album_rating and release_title: 
                if artist_name not in all_artists:
                    all_artists[artist_name] = {
                        'artist_name': artist_name,
                        'link': link,
                        'total_ratings': 0,
                        'rating_sum': 0,
                        'average_rating': 0,
                        'unique_releases': set(), 
                        'weighted_rating': 0
                    }
                
                # Aggregate ratings and add release title
                all_artists[artist_name]['total_ratings'] += 1
                all_artists[artist_name]['rating_sum'] += album_rating
                all_artists[artist_name]['unique_releases'].add(release_title)

    # Remove artists with fewer than 5 ratings
    filtered_artists = {
        name: artist for name, artist in all_artists.items() if artist['total_ratings'] >= 5
    }

    # Compute average rating and weighted rating for each artist
    W1, W2, W3 = 14, 0.07, 0.05
    for artist in filtered_artists.values():
        artist['average_rating'] = artist['rating_sum'] / artist['total_ratings']
        avg_ratings_per_release = artist['total_ratings'] / len(artist['unique_releases']) if len(artist['unique_releases']) > 0 else 0
        artist['weighted_rating'] = (
            (artist['average_rating'] * W1) + 
            (artist['total_ratings'] * W2) + 
            (len(artist['unique_releases']) * W3 * avg_ratings_per_release)
        )


    # Format average rating for output
    for artist in filtered_artists.values():
        artist['average_rating'] = f"{artist['average_rating']:.2f}"

    if not filtered_artists:
        return "No rated artists found."

    # Sort artists by their weighted rating in descending order
    sorted_artists = sorted(filtered_artists.values(), key=lambda x: x['weighted_rating'], reverse=True)

    # Limit the results to the top 100 artists
    top_artists = sorted_artists[:100]

    return top_artists


def save():
    with lzma.open('cache/ratings_cache_tmp.lzma', 'wb') as file:
        pickle.dump(ratings_cache, file)
    print("Ratings cache saved.")
    shutil.move("cache/ratings_cache_tmp.lzma", "cache/ratings_cache.lzma")