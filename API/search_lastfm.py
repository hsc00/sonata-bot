import requests
from bs4 import BeautifulSoup
import re
import logging

def get_album_info_from_lastfm(artist_name, album_name, lastfm_api_key):
    lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={lastfm_api_key}&artist={artist_name}&album={album_name}&format=json"
    lastfm_response = requests.get(lastfm_url)
    lastfm_data = lastfm_response.json()
    album_cover_url = lastfm_data['album']['image'][-1]['#text'] if 'album' in lastfm_data and 'image' in lastfm_data['album'] else None
    album_wiki = clean_wiki_text(lastfm_data['album']['wiki']['content']) if 'album' in lastfm_data and 'wiki' in lastfm_data['album'] else None
    return album_cover_url, album_wiki

def search_lastfm_artist(artist_name, lastfm_api_key):
    try:
        lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&api_key={lastfm_api_key}&artist={artist_name}&format=json"
        lastfm_response = requests.get(lastfm_url)
        lastfm_data = lastfm_response.json()

        url = lastfm_data['artist']['url']
        #Scrap to get the image
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the div with the background image
        div = soup.find('div', class_='header-new-background-image')
        if div and 'style' in div.attrs:
            # Extract the URL from the style attribute
            style = div['style']
            start = style.find('url(') + 4
            end = style.find(')', start)
            image_url = style[start:end]
        else:
            image_url = ""
            print("Image not found for artist: {artist_name}")

        artist_info = {
            # "name": lastfm_data['artist']['name'] if 'artist' in lastfm_data else None,
            "artist_img_url": image_url,
            "listeners": lastfm_data['artist']['stats']['listeners'] if 'artist' in lastfm_data and 'stats' in lastfm_data['artist'] else None,
            "similar_artists": [sim_artist['name'] for sim_artist in lastfm_data['artist']['similar']['artist']] if 'artist' in lastfm_data and 'similar' in lastfm_data['artist'] else [],
            "summary": lastfm_data['artist']['bio']['summary'] if 'artist' in lastfm_data and 'bio' in lastfm_data['artist'] else None
        }
        
        return artist_info
    except Exception as e:
        logging.error(f"Error during Last.fm search: {e}")
        return None


def clean_wiki_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        a.replace_with(f"[Read more]({a['href']})")
    text = soup.get_text()
    text = re.sub('User-contributed text is available under the Creative Commons By-SA License; additional terms may apply\.', '', text)
    return text
