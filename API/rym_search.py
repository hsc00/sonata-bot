import requests
import re
import logging
from bs4 import BeautifulSoup
from .cache import get_album_from_cache, add_album_to_cache, update_album_in_cache, update_likes_dislikes

def search_rym(query, google_tokens, cse_id, lastfm_api_key):
    # Check if the query is a plain text or link
    if 'rateyourmusic.com/' not in query:
        query += " site:rateyourmusic.com"

    # Use Google API to search for the RYM link and fetch album info
    for token in google_tokens:
        try:
            search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={token}&cx={cse_id}"
            response = requests.get(search_url)
            if response.status_code == 429:
                logging.warning(f"Rate limit exceeded for token {token}, retrying with next token.")
                continue
            results = response.json().get('items', [])
            if results:
                link = results[0]['link']
                cached_album = get_album_from_cache(link)
                if cached_album:
                    if cached_album['request_count'] > 5:
                        # Reset request_count and check online again
                        cached_album['request_count'] = 0
                        update_album_in_cache(link, cached_album)
                    else:
                        update_album_in_cache(link, cached_album)
                        return cached_album

                album_data = extract_album_info(results[0])
                album_data['link'] = link

                # Check if no release was found
                if album_data['release_name'] == 'Unknown Album': 
                    return None

                # Get album cover and wiki info from Last.fm API
                lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={lastfm_api_key}&artist={album_data['artist_name']}&album={album_data['release_name']}&format=json"
                lastfm_response = requests.get(lastfm_url)
                lastfm_data = lastfm_response.json()
                album_data['album_cover_url'] = lastfm_data['album']['image'][-1]['#text'] if 'album' in lastfm_data and 'image' in lastfm_data['album'] else None
                album_data['album_wiki'] = clean_wiki_text(lastfm_data['album']['wiki']['content']) if 'album' in lastfm_data and 'wiki' in lastfm_data['album'] else None

                # Get streaming links
                album_data['streaming_links'] = get_streaming_links(album_data['artist_name'], album_data['release_name'], album_data['release_year'])

                # Add or update album info in cache
                cached_album = get_album_from_cache(link)
                if cached_album:
                    cached_album['request_count'] += 1  # Increment request_count
                    update_album_in_cache(link, cached_album)
                    print(f"Updated cached album: {album_data['release_name']}")
                else:
                    album_data['request_count'] = 1  # Initialize request_count to 1
                    add_album_to_cache(link, album_data)
                    print(f"Added new album to cache: {album_data['release_name']}")

                return album_data
        except Exception as e:
            logging.error(f"Error during Google search with token {token}: {e}")
    logging.warning('No RYM link found')
    return None

def get_streaming_links(artist, album, year):
    query = f"{artist} {album} {year} streaming"
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
    release_year_match = re.search(r'Released (\d{1,2} \w+ \d{4})', description)
    if not release_year_match:
        release_year_match = re.search(r'Released (\w+ \d{4})', description)
    if not release_year_match:
        release_year_match = re.search(r'Released (\d{4})', description)
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
