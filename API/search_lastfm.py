import requests
from bs4 import BeautifulSoup
import re

def get_album_info_from_lastfm(artist_name, album_name, lastfm_api_key):
    lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={lastfm_api_key}&artist={artist_name}&album={album_name}&format=json"
    lastfm_response = requests.get(lastfm_url)
    lastfm_data = lastfm_response.json()
    album_cover_url = lastfm_data['album']['image'][-1]['#text'] if 'album' in lastfm_data and 'image' in lastfm_data['album'] else None
    album_wiki = clean_wiki_text(lastfm_data['album']['wiki']['content']) if 'album' in lastfm_data and 'wiki' in lastfm_data['album'] else None
    return album_cover_url, album_wiki

def get_artist_info_from_lastfm(artist_name, lastfm_api_key):
    lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&api_key={lastfm_api_key}&artist={artist_name}&format=json"
    lastfm_response = requests.get(lastfm_url)
    lastfm_data = lastfm_response.json()
    artist_bio = clean_wiki_text(lastfm_data['artist']['bio']['content']) if 'artist' in lastfm_data and 'bio' in lastfm_data['artist'] else None
    artist_image_url = lastfm_data['artist']['image'][-1]['#text'] if 'artist' in lastfm_data and 'image' in lastfm_data['artist'] else None
    return artist_bio, artist_image_url

def clean_wiki_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        a.replace_with(f"[Read more]({a['href']})")
    text = soup.get_text()
    text = re.sub('User-contributed text is available under the Creative Commons By-SA License; additional terms may apply\.', '', text)
    return text
