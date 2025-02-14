import json
import os
import unicodedata
import re

ARTIST_CACHE_FILE = 'cache/artist-cache.json'

def normalize_name(s):
    # Remove special characters and normalize the string
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[^\w\s-]', '', s)
    s = s.replace(' ', '-').lower()
    return s

def load_cache():
    if os.path.exists(ARTIST_CACHE_FILE):
        with open(ARTIST_CACHE_FILE, 'r') as file:
            return json.load(file)
    else:
        # Create the file if it doesn't exist
        with open(ARTIST_CACHE_FILE, 'w') as f:
            json.dump({}, f) 

def save_cache(cache):
    with open(ARTIST_CACHE_FILE, 'w') as file:
        json.dump(cache, file, indent=4)

def add_artist_to_cache(artist_name, artist_data):
    cache = load_cache()
    normalized_name = normalize_name(artist_name)

    cached_artist_data = cache.setdefault(normalized_name, {})

    artist_data['liked_users'] = cached_artist_data.get('liked_users', [])
    artist_data['disliked_users'] = cached_artist_data.get('disliked_users', [])

    artist_data['request_count'] = 1

    cache[normalized_name] = artist_data
    save_cache(cache)
    print(f"Added {artist_name} to cache")


def update_artist_in_cache(artist_name, artist_data):
    cache = load_cache()
    normalized_name = normalize_name(artist_name)
    if 'liked_users' not in artist_data:
        artist_data['liked_users'] = []
    if 'disliked_users' not in artist_data:
        artist_data['disliked_users'] = []
    
    cache[normalized_name] = artist_data
    save_cache(cache)

def update_artist_likes_dislikes(artist_name, user_id, like=True):
    cache = load_cache()
    normalized_name = normalize_name(artist_name)
    if normalized_name in cache:
        artist_data = cache[normalized_name]
        artist_data.setdefault('liked_users', [])
        artist_data.setdefault('disliked_users', [])
        if like:
            if user_id not in artist_data['liked_users']:
                artist_data['liked_users'].append(user_id)
            else:
                artist_data['liked_users'].remove(user_id)
            if user_id in artist_data['disliked_users']:
                artist_data['disliked_users'].remove(user_id)
        else:
            if user_id not in artist_data['disliked_users']:
                artist_data['disliked_users'].append(user_id)
            else:
                artist_data['disliked_users'].remove(user_id)
            if user_id in artist_data['liked_users']:
                artist_data['liked_users'].remove(user_id)
        save_cache(cache)
        print(f"Updated cache for {normalized_name}")
    else:
        print(f"Link not found in artist cache: {normalized_name}")

def get_artist_from_cache(artist_name, increment_request_count=True):
    cache = load_cache()
    normalized_name = normalize_name(artist_name)
    if normalized_name in cache:
        artist_data = cache[normalized_name]
        if increment_request_count:
            artist_data.setdefault('request_count', 0)
            artist_data['request_count'] += 1
        artist_data.setdefault('liked_users', [])
        artist_data.setdefault('disliked_users', [])
        save_cache(cache)
        print(f"Retrieved from cache for {normalized_name}")
        return artist_data
    print(f"Link not found in artist cache: {normalized_name}")
    return None

def get_most_loved_hated_artists(data_type):
    cache = load_cache()
    artists = [
        (artist_name, len(artist_data.get(f'{data_type}_users', [])))
        for artist_name, artist_data in cache.items()
        if len(artist_data.get(f'{data_type}_users', [])) > 0
    ]
    # Sort the list in descending order
    artists.sort(key=lambda x: x[1], reverse=True)
    # Get the top 100 releases or all releases with at least one like
    top_artists = artists[:100]
    # Retrieve album data for the top releases, maintaining the order
    top_artists_data = [
        {
            'artist_name': cache[artist_name]['artist_name'],
            'link': cache[artist_name].get('link', ''),
            'artist_img_url': cache[artist_name].get('artist_img_url', ''),
            f'{data_type}_users': cache[artist_name].get(f'{data_type}_users', [])
        }
        for artist_name, _ in top_artists
        if 'artist_name' in cache[artist_name]
    ]

    return top_artists_data