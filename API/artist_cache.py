import json
import os

CACHE_FILE = 'cache/artist-cache.json'

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

def get_artist_from_cache(link, increment_request_count=True):
    return None

def update_artist_in_cache(link, album_data):
    return None