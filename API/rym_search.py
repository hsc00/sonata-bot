import re
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from .album_cache import *
from .artist_cache import *
from .search_lastfm import get_album_info_from_lastfm
from API.search_lastfm import search_lastfm_artist
from .google_search import *


def search_rym_release(release_name, google_tokens, cse_id, cse_streaming, lastfm_api_key):
    # Regex patterns
    rym_pattern = re.compile(r'https://rateyourmusic.com/release/(album|mixtape|ep|single|musicvideo|comp|unauth|video|additional)/')
    dash_pattern = re.compile(r'\s*-\s*')

    def fetch_google_results(release_name):
        return google_search(release_name, google_tokens, cse_id)

    if 'rateyourmusic.com/release/' in release_name:
        release_name = rym_pattern.sub('', release_name).replace('/', ' ').replace('-', ' ').strip()
    else:
        release_name = dash_pattern.sub(' ', release_name).strip()

    cached_album = get_album_from_cache(release_name)
    if cached_album and cached_album['request_count'] <= 5:
        return cached_album

    album_data = None
    with ThreadPoolExecutor(max_workers=5) as executor:
        google_future = executor.submit(fetch_google_results, release_name)
        google_results = google_future.result()

    if google_results:
        for result in google_results:
            link = result['link']
            if link.startswith('https://rateyourmusic.com/release/') and all(word.lower() in link.lower() for word in release_name.split()):
                album_data = extract_album_info(result)
                album_data['link'] = link
                break   

    if album_data:
        album_cover_url, album_wiki = get_album_info_from_lastfm(album_data['artist_name'], album_data['release_name'], lastfm_api_key)
        album_data['album_cover_url'] = album_cover_url
        album_data['album_wiki'] = album_wiki
        album_data['streaming_links'] = get_streaming_links("release", album_data['artist_name'], album_data['release_name'], album_data['release_year'], google_tokens, cse_streaming)

        cached_album = get_album_from_cache(album_data['artist_name'] + "-" + album_data['release_name'])
        if cached_album and cached_album['request_count'] > 5:
            cached_album['request_count'] = 1
            update_album_in_cache(album_data['artist_name'] + "-" + album_data['release_name'], cached_album)
            return cached_album
        else:
            album_data['request_count'] = 1
            add_album_to_cache(album_data['artist_name'] + "-" + album_data['release_name'], album_data)
    else:
        print("Album not found.")

    return album_data
    

def search_rym_artist(artist_query, google_tokens, cse_id, cse_streaming, lastfm_api_key):
    def fetch_google_results(query):
        return google_search(query, google_tokens, cse_id)

    artist_name = artist_query if 'rateyourmusic.com/' not in artist_query else re.sub(r'[\W_]+', ' ', artist_query.split('/')[-1])

    cached_artist = get_artist_from_cache(artist_name)
    if cached_artist:
        if cached_artist['request_count'] <= 5:
            return cached_artist

    artist_info = None
    with ThreadPoolExecutor() as executor:
        google_future = executor.submit(fetch_google_results, artist_name)
        google_results = google_future.result()
        
        if google_results:
            for result in google_results:
                link = result['link']
                if link.startswith('https://rateyourmusic.com/artist/') and all(word.lower() in link.lower() for word in artist_name.split()):
                    rym_info = extract_artist_info(result) or {}
                    rym_info['link'] = link
                    lastfm_info = search_lastfm_artist(artist_name, lastfm_api_key) or {}
                    
                    if rym_info and lastfm_info:
                        cached_artist = get_artist_from_cache(rym_info['artist_name'])
                        if cached_artist:
                            if cached_artist['request_count'] > 5:
                                cached_artist['request_count'] = 1
                                update_artist_in_cache(rym_info['artist_name'], cached_artist)
                                return cached_artist
                            else:
                                cached_artist['request_count'] = 1

                        artist_info = {**rym_info, **lastfm_info}
                        artist_info['streaming_links'] = get_streaming_links("artist", rym_info['artist_name'], "", "", google_tokens, cse_streaming)
                        add_artist_to_cache(rym_info['artist_name'], artist_info)
                    else:        
                        print("Artist not found.")
        
    return artist_info


def get_streaming_links(action_type, artist, album, year, google_tokens, cse_streaming):
    # Check if streaming links are already in cache
    if action_type == "release" : 
        cached_album = get_album_from_cache(f"{artist}-{album}", increment_request_count=False)
        if cached_album and 'streaming_links' in cached_album:
            return cached_album['streaming_links']
    elif action_type == "artist" : 
        cached_artist = get_artist_from_cache(f"{artist}", increment_request_count=False)
        if cached_artist and 'streaming_links' in cached_artist:
            return cached_artist['streaming_links']
    
    # Initial query and action
    if action_type == "release": query = f"{artist} - {album} album"
    elif action_type == "artist": query = artist

    streaming_links = search_streaming_links(query, google_tokens, cse_streaming)
    if streaming_links:
        return streaming_links
    
    print("No streaming links found.")
    return None


def extract_album_info(result):
    pagemap = result.get('pagemap', {})
    musicalbum = pagemap.get('musicalbum', [{}])[0]
    aggregaterating = pagemap.get('aggregaterating', [{}])[0]
    metatags = pagemap.get('metatags', [{}])[0]

    artist_name = pagemap.get('musicgroup', [{}])[0].get('name', 'Unknown Artist')
    release_name = musicalbum.get('name', 'Unknown Album')
    rym_cover_url = pagemap.get('cse_thumbnail', [{}])[0].get('src', '')
    og_description = metatags.get('og:description', '')

    release_year = extract_release_year(og_description)
    genres = extract_genres(og_description)
    best_album_position = extract_best_album_position(og_description)
    all_time_album_position = extract_all_time_album_position(og_description)
    performers = extract_performers(og_description)

    rating_value = aggregaterating.get('ratingvalue', 'No Rating')
    rating_count = aggregaterating.get('ratingcount', 'No Ratings')
    formatted_rating_count = f"{int(rating_count):,}" if rating_count.isdigit() else rating_count

    return {
        'artist_name': artist_name,
        'release_name': release_name,
        'rym_cover_url': rym_cover_url,
        'release_year': release_year,
        'genres': genres,
        'rating_value': rating_value,
        'formatted_rating_count': formatted_rating_count,
        'best_album_position': best_album_position,
        'all_time_album_position': all_time_album_position,
        'performers': performers
    }


def extract_artist_info(result):
    pagemap = result.get('pagemap', {})
    metatags = pagemap.get('metatags', [{}])[0]

    artist_name = pagemap.get('musicgroup', [{}])[0].get('name', 'Unknown Artist')
    rym_img_url = pagemap.get('cse_thumbnail', [{}])[0].get('src', '')
    og_description = metatags.get('og:description', '')
    founded_year = extract_founded_or_born_year(og_description)
    genres = extract_genres(og_description)

    return {
        'artist_name': artist_name,
        'rym_img_url': rym_img_url,
        'founded_year': founded_year,
        'genres': genres,
    }


def extract_founded_or_born_year(description):
    # Try to find a pattern for "formed" or "born"
    patterns = [
        r'(formed|born) (\d{1,2} \w+ \d{4})',  # formed/born DAY MONTH YEAR
        r'(formed|born) (\w+ \d{4})',          # formed/born MONTH YEAR
        r'(formed|born) (\d{4})'               # formed/born YEAR
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return f"{match.group(1).capitalize()} in: {match.group(2).split()[-1]}"
    
    # Return 'Unknown' if no match is found
    return 'Unknown'


def extract_release_year(description):
    # Try to find a date pattern like "Released 12 January 2023"
    release_year_match = re.search(r'Released (\d{1,2} \w+ \d{4})', description)
    if not release_year_match:
        # Try to find a date pattern like "Released January 2023"
        release_year_match = re.search(r'Released (\w+ \d{4})', description)
    if not release_year_match:
        # Try to find a date pattern like "Released 2023"
        release_year_match = re.search(r'Released (\d{4})', description)
    if not release_year_match:
        # Try to find a date pattern like "Released in November 2023"
        release_year_match = re.search(r'Released in (\w+ \d{4})', description)
    # Extract and return the year part of the date, or 'Unknown Year' if no match is found
    return release_year_match.group(1).split()[-1] if release_year_match else 'Unknown Year'


def extract_genres(description):
    genres_match = re.search(r'Genres: (.+?)\.', description)
    return genres_match.group(1) if genres_match else 'Unknown Genres'

def extract_best_album_position(description):
    best_album_match = re.search(r'#(\d+) in the best albums of (\d{4})', description)
    return f"#{best_album_match.group(1)} of {best_album_match.group(2)}" if best_album_match else None

def extract_all_time_album_position(description):
    all_time_album_match = re.search(r'#(\d+) of all time album', description)
    return f"#{all_time_album_match.group(1)} overall" if all_time_album_match else None

def extract_performers(description):
    performers_match = re.search(r'Featured (?:performers|peformers): (.+)', description)
    return performers_match.group(1) if performers_match else None

def clean_wiki_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        a.replace_with(f"[Read more]({a['href']})")
    text = soup.get_text()
    # Remove the specific sentence if it starts with "User-contributed text"
    text = re.sub('User-contributed text is available under the Creative Commons By-SA License; additional terms may apply\.', '', text)
    return text