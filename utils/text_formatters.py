import json
import os
import re

import urllib


def add_newline_limit(text, limit=45):
    if len(text) <= limit:
        return text
    
    # Find the last space within the limit
    cut_off = text[:limit].rfind(" ")
    if cut_off == -1:  # If no space is found, split at the limit
        cut_off = limit

    # Insert a newline after the last word within the limit
    return text[:cut_off] + "\n" + text[cut_off:].strip()

def get_user_id(string):
    # Use regex to find the user id
    match = re.search(r'<@(\d+)>', string)
    if match:
        user_id = match.group(1)  # Extract only the numeric part
        # Remove the user id from the original string
        release_query = re.sub(r'<@\d+>', '', string).strip()
        return release_query, user_id  # Return the modified string and user_id separately
    
    return string, None  # Return original string and None if no mention is found

def rm_special_chars(string):
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', string)

    return cleaned_text.strip()

def rating_to_emoji(rating):
    digit_to_emoji = {
        0: "0️⃣",
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣"
    }
    integer_part = int(rating)
    remainder = rating - integer_part
    emoji_label = digit_to_emoji.get(integer_part, str(integer_part))
    if remainder >= 0.5:
        emoji_label += "." + digit_to_emoji[5]
    else:
        emoji_label += "." + digit_to_emoji[0]
    return emoji_label

def format_count(count):
    if count >= 1000:
        return f"{count/1000:.1f}k".rstrip('0').rstrip('.')
    return str(count)

def rym_artist_url_creator(string):
    cleaned_artist_name = rm_special_chars(string).lower()
    cleaned_url = cleaned_artist_name.replace(' ', '-')

    return cleaned_url

def rym_release_url_creator(artist_name, release_name):
    link = f"https://rateyourmusic.com/search?searchtype=a&searchterm={urllib.parse.quote(artist_name + ' ' + release_name)}&searchtype="
    
    return link

def rym_artist_url_creator(artist_name):
    link = f"https://rateyourmusic.com/search?searchtype=a&searchterm={urllib.parse.quote(artist_name)}&searchtype=artist"
    
    return link

def rym_user_url_creator(user_id):
    cache_file = 'cache/rym-cache.json'

    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    if user_id in data:
        rym_username = data[user_id]
        url = f"https://rateyourmusic.com/~{rym_username}"
    else:
        url = None

    return url