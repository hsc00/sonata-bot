import re
import requests
from bs4 import BeautifulSoup
import logging
import json
from config import lastfm_api_key

def fetch_json(url):
    """Fetches JSON data from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException as e:
        logging.error(f"Error fetching data from URL: {e}")
        return None

def extract_image_url(url):
    """Extracts the background image URL from the artist's Last.fm page."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('div', class_='header-new-background-image')

        if div and 'style' in div.attrs:
            style = div['style']
            start = style.find('url(') + 4
            end = style.find(')', start)
            return style[start:end]
    
        else:
            logging.warning(f"Image not found for URL: {url}")
            return None
        
    except requests.RequestException as e:
        logging.error(f"Error scraping image URL: {e}")

        return None

def clean_wiki_text(html):
    """Cleans the HTML content from the Last.fm wiki and formats 'Read more' links."""
    soup = BeautifulSoup(html, 'html.parser')

    for a in soup.find_all('a'):
        a.replace_with(f"[Read more]({a['href']})")
    text = soup.get_text()
    text = re.sub(r'User-contributed text is available under the Creative Commons By-SA License; additional terms may apply\.', '', text)
    
    return re.sub(r'\s+', ' ', text).strip()

def clean_summary(summary):
    """Extracts and cleans the summary text from the Last.fm wiki."""
    # Limit text to 1200 chars
    read_more_link_start = summary.rfind("[Read more](")
    read_more_link = summary[read_more_link_start:] if read_more_link_start != -1 else ''
    max_length = 1200 - len(read_more_link)

    if len(summary) > max_length:
        # Ensure we do not cut off in the middle of a word
        truncated_summary = summary[:max_length].rsplit(' ', 1)[0]
        summary = truncated_summary + '...' + read_more_link
    elif read_more_link and not summary.endswith(read_more_link):
        summary = summary + ' ' + read_more_link

    return summary

def get_album_info_from_lastfm(artist_name, album_name):
    """Fetches album information from Last.fm."""
    lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={lastfm_api_key}&artist={artist_name}&album={album_name}&format=json"
    lastfm_data = fetch_json(lastfm_url)

    if lastfm_data and 'album' in lastfm_data:
        album_cover_url = lastfm_data['album']['image'][-1]['#text'] if 'image' in lastfm_data['album'] else None
        album_wiki = clean_wiki_text(lastfm_data['album']['wiki']['content']) if 'wiki' in lastfm_data['album'] else None

        if album_wiki:
            read_more_link_start = album_wiki.rfind("[Read more](")
            read_more_link = album_wiki[read_more_link_start:] if read_more_link_start != -1 else ''
            max_length = 1200 - len(read_more_link)

            if len(album_wiki) > max_length:
                album_wiki = album_wiki[:max_length-3].rsplit(' ', 1)[0] + '...' + read_more_link
            elif read_more_link and not album_wiki.endswith(read_more_link):
                album_wiki += read_more_link

        return album_cover_url, album_wiki
    
    return None, None

def search_lastfm_artist(artist_name):
    """Fetches artist information from Last.fm"""
    lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&api_key={lastfm_api_key}&artist={artist_name}&format=json"
    lastfm_data = fetch_json(lastfm_url)
    
    if lastfm_data and 'artist' in lastfm_data:
        url = lastfm_data['artist']['url']
        image_url = extract_image_url(url)
        listeners = lastfm_data['artist']['stats'].get('listeners') if 'stats' in lastfm_data['artist'] else None
        formatted_listeners = f"{int(listeners):,}" if listeners and listeners.isdigit() else listeners
        summary = clean_wiki_text(lastfm_data['artist']['bio']['summary']) if 'bio' in lastfm_data['artist'] else None
        summary = clean_summary(summary)

        return {
            "artist_img_url": image_url,
            "listeners": formatted_listeners,
            "similar_artists": [sim_artist['name'] for sim_artist in lastfm_data['artist']['similar']['artist']] if 'similar' in lastfm_data['artist'] else [],
            "summary": summary
        }
    return None

def get_lastfm_track(user_id, data_type):
    """Checks if a user's Discord ID is in the lastfm-cache.json file."""
    try:
        with open('cache/lastfm-cache.json', 'r') as f:
            data = json.load(f)
            last_fm_username = data.get(str(user_id))
            if last_fm_username:
                return get_last_played(last_fm_username, lastfm_api_key, data_type)
            else:
                return None
    except FileNotFoundError:
        return False 

def clean_name(name):
    # Remove (remaster) and similar variants within parentheses
    name = re.sub(r'\s*\([^)]*remaster[^)]*\)', '', name, flags=re.IGNORECASE)
    # Remove remaster variants with hyphens or standalone
    name = re.sub(r'(\s*-\s*)?remaster(ed)?(\s*-\s*)?', '', name, flags=re.IGNORECASE)
    # Clean up extra whitespace and any trailing hyphens
    return re.sub(r'\s*-\s*$', '', name.strip())


def get_last_played(last_fm_username, api_key, data_type):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={last_fm_username}&api_key={api_key}&format=json"
    response = requests.get(url)
    data = response.json()
    if 'recenttracks' in data and 'track' in data['recenttracks']:
        last_track = data['recenttracks']['track'][0]
        track_name = clean_name(last_track['name'])
        artist_name = last_track['artist']['#text']
        album_name = clean_name(last_track['album']['#text'])
        if data_type == 'release':
            return f'{artist_name} - {album_name}'
        elif data_type == 'artist':
            return artist_name
    else:
        return None