import json
import os
import unicodedata
import re

CACHE_FILE = 'cache/album-cache.json'

def normalize_name(s):
    # Remove special characters and normalize the string
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[^\w\s-]', '', s)
    s = s.replace(' ', '-').lower()
    return s

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file, indent=4)


def add_album_to_cache(release_name, album_data):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    album_data['request_count'] = 1
    album_data['likes'] = 0
    album_data['dislikes'] = 0
    album_data['liked_users'] = []
    album_data['disliked_users'] = []
    cache[normalized_name] = album_data
    save_cache(cache)
    print(f"Added {normalized_name} to cache")

def update_album_in_cache(release_name, album_data):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    album_data.setdefault('likes', 0)
    album_data.setdefault('dislikes', 0)
    album_data.setdefault('liked_users', [])
    album_data.setdefault('disliked_users', [])
    cache[normalized_name] = album_data
    save_cache(cache)
    print(f"Updated {normalized_name}")


def update_releases_likes_dislikes(release_name, user_id, like=True):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    if normalized_name in cache:
        album_data = cache[normalized_name]
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
        print(f"Updated cache for {normalized_name}")
    else:
        print(f"Link not found in release cache: {normalized_name}")

def get_album_from_cache(release_name, increment_request_count=True):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    if normalized_name in cache:
        album_data = cache[normalized_name]
        if increment_request_count:
            album_data['request_count'] += 1
        album_data.setdefault('likes', 0)
        album_data.setdefault('dislikes', 0)
        album_data.setdefault('liked_users', [])
        album_data.setdefault('disliked_users', [])
        save_cache(cache)
        print(f"Retrieved from cache for {normalized_name}")
        return album_data
    print(f"Not found in release cache: {normalized_name}")
    return None
