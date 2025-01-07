import requests
import re
import logging
from bs4 import BeautifulSoup
from .album_cache import get_album_from_cache, add_album_to_cache, update_album_in_cache, update_likes_dislikes
from .artist_cache import get_artist_from_cache, update_artist_in_cache
from .search_lastfm import get_album_info_from_lastfm
from API.search_lastfm import search_lastfm_artist
from .google_search import google_search

def search_rym(query, google_tokens, cse_id, lastfm_api_key):
    if 'rateyourmusic.com/' not in query:
        query += " site:rateyourmusic.com"

    results = google_search(query, google_tokens, cse_id)
    if results:
        link = results[0]['link']
        cached_album = get_album_from_cache(link)
        if cached_album:
            if cached_album['request_count'] > 5:
                cached_album['request_count'] = 0
                update_album_in_cache(link, cached_album)
            else:
                update_album_in_cache(link, cached_album)
                return cached_album

        album_data = extract_album_info(results[0])
        album_data['link'] = link

        if album_data['release_name'] == 'Unknown Album': 
            return None

        album_cover_url, album_wiki = get_album_info_from_lastfm(album_data['artist_name'], album_data['release_name'], lastfm_api_key)
        album_data['album_cover_url'] = album_cover_url
        album_data['album_wiki'] = album_wiki

        album_data['streaming_links'] = get_streaming_links(album_data['artist_name'], album_data['release_name'], album_data['release_year'])

        cached_album = get_album_from_cache(link)
        if cached_album:
            update_album_in_cache(link, cached_album)
            print(f"Updated cached album: {album_data['release_name']}")
        else:
            album_data['request_count'] = 1
            add_album_to_cache(link, album_data)
            print(f"Added new album to cache: {album_data['release_name']}")

        return album_data


def search_rym_artist(artist_query, google_tokens, cse_id, lastfm_api_key):
    if 'rateyourmusic.com/' not in artist_query:
        artist_name = artist_query
        artist_query += " site:rateyourmusic.com"
        for token in google_tokens:
            try:
                search_url = f"https://www.googleapis.com/customsearch/v1?q={artist_query}&key={token}&cx={cse_id}"
                response = requests.get(search_url)
                if response.status_code == 429:
                    logging.warning(f"Rate limit exceeded for token {token}, retrying with next token.")
                    continue
                results = response.json().get('items', [])
                if results:
                    for result in results:
                        link = result['link']
                            
            except Exception as e:
                logging.error(f"Error during Google search with token {token}: {e}")

        lastfm_info = search_lastfm_artist(artist_name, lastfm_api_key)

        return lastfm_info
    else:
        artist_name = artist_query.split('/')[-1] 
        if link.startswith('https://rateyourmusic.com/artist/'):
            cached_artist = get_artist_from_cache(link)
            if cached_artist:
                if cached_artist['request_count'] > 5:
                    cached_artist['request_count'] = 0
                    update_artist_in_cache(link, cached_artist)
                else:
                    update_artist_in_cache(link, cached_artist)
                    artist_query = cached_artist
            artist_data = results[0]
            artist_data['link'] = link
            return search_lastfm_artist(artist_name, lastfm_api_key)
        for token in google_tokens:
            try:
                search_url = f"https://www.googleapis.com/customsearch/v1?q={artist_query}&key={token}&cx={cse_id}"
                response = requests.get(search_url)
                if response.status_code == 429:
                    logging.warning(f"Rate limit exceeded for token {token}, retrying with next token.")
                    continue
                results = response.json().get('items', [])
                if results:
                    for result in results:
                        link = result['link']
                            
            except Exception as e:
                logging.error(f"Error during Google search with token {token}: {e}")


def get_streaming_links(artist, album, year):
    # Remove all - from the original names and then replace spaces with - for the url
    formatted_artist = artist.replace('-', '').replace(' ', '-').lower()
    formatted_album = album.replace('-', '').replace(' ', '-').lower()

    # Check if streaming links are already in cache
    cached_album = get_album_from_cache(f"rateyourmusic.com/release/album/{artist}/{album}", increment_request_count=False)

    if cached_album and 'streaming_links' in cached_album:
        return cached_album['streaming_links']
    query = f"{formatted_artist}-{formatted_album}-{year} streaming"
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    streaming_links = []
    for div in soup.find_all('div', {'data-attrid': 'action:listen_album'}):
        for a in div.find_all('a', href=True):
            href = a['href']
            if any(service in href for service in ['spotify', 'apple', 'youtube', 'soundcloud', 'bandcamp']):
                streaming_links.append(href)

    # Update cache with streaming links
    if cached_album:
        cached_album['streaming_links'] = streaming_links
        update_album_in_cache(f"rateyourmusic.com/release/album/{formatted_artist}/{formatted_album}", cached_album)

    return streaming_links


def extract_album_info(result):
    pagemap = result.get('pagemap', {})
    musicalbum = pagemap.get('musicalbum', [{}])[0]
    aggregaterating = pagemap.get('aggregaterating', [{}])[0]
    metatags = pagemap.get('metatags', [{}])[0]

    artist_name = pagemap.get('musicgroup', [{}])[0].get('name', 'Unknown Artist')
    release_name = musicalbum.get('name', 'Unknown Album')
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
        'release_year': release_year,
        'genres': genres,
        'rating_value': rating_value,
        'formatted_rating_count': formatted_rating_count,
        'best_album_position': best_album_position,
        'all_time_album_position': all_time_album_position,
        'performers': performers
    }

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

def handle_like_dislike(link, user_id, like=True):
    update_likes_dislikes(link, user_id, like)
