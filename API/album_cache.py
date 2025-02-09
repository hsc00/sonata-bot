import json
import os
import unicodedata
import re
import datetime

CACHE_FILE = 'cache/album-cache.json'

import unicodedata
import re

def normalize_name(s):
    # Remove special characters and normalize the string
    s = unicodedata.normalize('NFKD', s)
    # Remove any special characters, replace spaces with hyphens, convert to lowercase
    s = re.sub(r'[^\w\s-]', '', s).replace(' ', '-').lower()
    # Remove any leading hyphens and replace multiple hyphens with a single hyphen
    s = re.sub(r'^-+|-+$', '', re.sub(r'-+', '-', s))
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
    album_data['liked_users'] = []
    album_data['disliked_users'] = []
    cache[normalized_name] = album_data
    save_cache(cache)
    print(f"Added {normalized_name} to cache")

def update_album_in_cache(release_name, album_data):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    album_data.setdefault('liked_users', [])
    album_data.setdefault('disliked_users', [])
    cache[normalized_name] = album_data
    save_cache(cache)
    print(f"Updated {normalized_name}")

def update_album_rating(release_name, rating_info):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    album_data = cache.get(normalized_name, {})
    timestamp = datetime.datetime.now().isoformat()
    # Refresh current info
    album_data['rating_value'] = rating_info['rating_value']
    album_data['formatted_rating_count'] = rating_info['formatted_rating_count']
    album_data['best_album_position'] = rating_info['best_album_position']
    album_data['all_time_album_position'] = rating_info['all_time_album_position']
    
    # Update rating value history
    rating_history = album_data.get('rating_history', [])
    if not rating_history or rating_history[-1]['value'] != rating_info['rating_value']:
        rating_history.append({'value': rating_info['rating_value'], 'timestamp': timestamp})
        album_data['rating_history'] = rating_history
        
        # Only update if rating_history changes
        # Update rating count history
        rating_count_history = album_data.get('rating_count_history', [])
        rating_count_history.append({'count': rating_info['formatted_rating_count']})
        album_data['rating_count_history'] = rating_count_history
        
        # Update best album position history
        year_position_history = album_data.get('year_position_history', [])
        year_position_history.append({'position': rating_info['best_album_position']})
        album_data['year_position_history'] = year_position_history
        
        # Update all-time album position history
        all_time_position_history = album_data.get('all_time_position_history', [])
        all_time_position_history.append({'position': rating_info['all_time_album_position']})
        album_data['all_time_position_history'] = all_time_position_history
 
        cache[normalized_name] = album_data
        save_cache(cache)
        print(f"Updated {normalized_name} rating info")
    overall_rating_history = get_album_rating_history(album_data)
    return overall_rating_history

def get_album_rating_history(album_data):
    rating_history = album_data.get('rating_history', [])
    rating_count_history = album_data.get('rating_count_history', [])
    year_position_history = album_data.get('year_position_history', [])
    all_time_position_history = album_data.get('all_time_position_history', [])
    
    return {
        'rating_history': rating_history,
        'rating_count_history': rating_count_history,
        'year_position_history': year_position_history,
        'all_time_position_history': all_time_position_history
    }

def update_releases_likes_dislikes(release_name, user_id, like=True):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    if normalized_name in cache:
        album_data = cache[normalized_name]
        album_data.setdefault('liked_users', [])
        album_data.setdefault('disliked_users', [])
        if like:
            if user_id not in album_data['liked_users']:
                album_data['liked_users'].append(user_id)
            if user_id in album_data['disliked_users']:
                album_data['disliked_users'].remove(user_id)
        else:
            if user_id not in album_data['disliked_users']:
                album_data['disliked_users'].append(user_id)
            if user_id in album_data['liked_users']:
                album_data['liked_users'].remove(user_id)
        save_cache(cache)
        print(f"Updated cache for {normalized_name}")
    else:
        print(f"Link not found in release cache: {normalized_name}")

def get_album_from_cache(release_name, increment_request_count=True):
    cache = load_cache()
    normalized_name = normalize_name(release_name)
    for key in cache:
        if normalized_name in key:
            album_data = cache[key]
            if increment_request_count:
                album_data['request_count'] += 1
            album_data.setdefault('liked_users', [])
            album_data.setdefault('disliked_users', [])
            save_cache(cache)
            print(f"Retrieved from cache for {normalized_name}")
            return album_data
    print(f"Not found in release cache: {normalized_name}")
    return None

def get_most_loved_releases():
    cache = load_cache()
    # Create a list of tuples (release_name, liked_users_count)
    loved_releases = [(release_name, len(album_data.get('liked_users', []))) for release_name, album_data in cache.items() if len(album_data.get('liked_users', [])) > 0]
    # Sort the list by liked_users_count in descending order
    loved_releases.sort(key=lambda x: x[1], reverse=True)
    # Get the top 100 releases or all releases with at least one like
    top_loved_releases = loved_releases[:100]
    # Retrieve album data for the top releases
    top_releases_data = [cache[release_name] for release_name, _ in top_loved_releases]
    return top_releases_data