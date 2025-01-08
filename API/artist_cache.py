import json
import os

ARTIST_CACHE_FILE = 'cache/artist-cache.json'

def normalize_url(url):
    if url.startswith('https://'):
        url = url.split('https://')[1]
    elif url.startswith('http://'):
        url = url.split('http://')[1]
    if url.startswith('www.'):
        url = url.split('www.')[1]
    return url.rstrip('/')

def load_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_cache(cache_file, cache):
    with open(cache_file, 'w') as file:
        json.dump(cache, file, indent=4)

def add_artist_to_cache(link, artist_data):
    cache = load_cache(ARTIST_CACHE_FILE)
    normalized_link = normalize_url(link)
    artist_data['request_count'] = 1
    artist_data['likes'] = 0
    artist_data['dislikes'] = 0
    artist_data['liked_users'] = []
    artist_data['disliked_users'] = []
    cache[normalized_link] = artist_data
    save_cache(ARTIST_CACHE_FILE, cache)

def update_artist_in_cache(link, artist_data):
    cache = load_cache(ARTIST_CACHE_FILE)
    normalized_link = normalize_url(link)
    
    if 'likes' not in artist_data:
        artist_data['likes'] = 0
    if 'dislikes' not in artist_data:
        artist_data['dislikes'] = 0
    if 'liked_users' not in artist_data:
        artist_data['liked_users'] = []
    if 'disliked_users' not in artist_data:
        artist_data['disliked_users'] = []
    
    cache[normalized_link] = artist_data
    save_cache(ARTIST_CACHE_FILE, cache)


def update_artist_likes_dislikes(link, user_id, like=True):
    cache = load_cache(ARTIST_CACHE_FILE)
    normalized_link = normalize_url(link)
    if normalized_link in cache:
        artist_data = cache[normalized_link]
        artist_data.setdefault('liked_users', [])
        artist_data.setdefault('disliked_users', [])
        if like:
            if user_id not in artist_data['liked_users']:
                artist_data['likes'] += 1
                artist_data['liked_users'].append(user_id)
            if user_id in artist_data['disliked_users']:
                artist_data['dislikes'] -= 1
                artist_data['disliked_users'].remove(user_id)
        else:
            if user_id not in artist_data['disliked_users']:
                artist_data['dislikes'] += 1
                artist_data['disliked_users'].append(user_id)
            if user_id in artist_data['liked_users']:
                artist_data['likes'] -= 1
                artist_data['liked_users'].remove(user_id)
        save_cache(ARTIST_CACHE_FILE, cache)
        print(f"Updated cache for {normalized_link}")
    else:
        print(f"Link not found in cache: {normalized_link}")

def get_artist_from_cache(link, increment_request_count=True):
    cache = load_cache(ARTIST_CACHE_FILE)
    normalized_link = normalize_url(link)
    if normalized_link in cache:
        artist_data = cache[normalized_link]
        if increment_request_count:
            artist_data['request_count'] += 1
        artist_data.setdefault('likes', 0)
        artist_data.setdefault('dislikes', 0)
        artist_data.setdefault('liked_users', [])
        artist_data.setdefault('disliked_users', [])
        save_cache(ARTIST_CACHE_FILE, cache)
        print(f"Retrieved from cache for {normalized_link}")
        return artist_data
    print(f"Link not found in cache: {normalized_link}")
    return None
