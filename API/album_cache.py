import json
import os

CACHE_FILE = 'cache/album-cache.json'
cache = {}

def normalize_url(url):
    if url.startswith('https://'):
        url = url.split('https://')[1]
    elif url.startswith('http://'):
        url = url.split('http://')[1]
    if url.startswith('www.'):
        url = url.split('www.')[1]
    return url.rstrip('/')

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file, indent=4)

load_cache()

def add_album_to_cache(link, album_data):
    normalized_link = normalize_url(link)
    album_data['request_count'] = 1
    album_data['likes'] = 0
    album_data['dislikes'] = 0
    album_data['liked_users'] = []
    album_data['disliked_users'] = []
    cache[normalized_link] = album_data
    save_cache(cache)

def update_album_in_cache(link, album_data):
    normalized_link = normalize_url(link)
    album_data.setdefault('likes', 0)
    album_data.setdefault('dislikes', 0)
    album_data.setdefault('liked_users', [])
    album_data.setdefault('disliked_users', [])
    cache[normalized_link] = album_data
    save_cache(cache)


def update_releases_likes_dislikes(link, user_id, like=True):
    normalized_link = normalize_url(link)
    if normalized_link in cache:
        album_data = cache[normalized_link]
        album_data.setdefault('liked_users', [])
        album_data.setdefault('disliked_users', [])
        if like:
            if user_id not in album_data['liked_users']:
                album_data['likes'] += 1
                album_data['liked_users'].append(user_id)
            if user_id in album_data['disliked_users']:
                album_data['dislikes'] -= 1
                album_data['disliked_users'].remove(user_id)
        else:
            if user_id not in album_data['disliked_users']:
                album_data['dislikes'] += 1
                album_data['disliked_users'].append(user_id)
            if user_id in album_data['liked_users']:
                album_data['likes'] -= 1
                album_data['liked_users'].remove(user_id)
        save_cache(cache)
        print(f"Updated cache for {normalized_link}")
    else:
        print(f"Link not found in release cache: {normalized_link}")

def get_album_from_cache(link, increment_request_count=True):
    normalized_link = normalize_url(link)
    if normalized_link in cache:
        album_data = cache[normalized_link]
        if increment_request_count:
            album_data['request_count'] += 1
        album_data.setdefault('likes', 0)
        album_data.setdefault('dislikes', 0)
        album_data.setdefault('liked_users', [])
        album_data.setdefault('disliked_users', [])
        save_cache(cache)
        print(f"Retrieved from cache for {normalized_link}")
        return album_data
    print(f"Link not found in release cache: {normalized_link}")
    return None
