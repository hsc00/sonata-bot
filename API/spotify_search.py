import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
load_dotenv()
spotify_id = os.getenv('SPOTIFY_ID')
spotify_secret = os.getenv('SPOTIFY_SECRET')

# not being used for now. getting links from google
def get_spotify_links(query):
    client_id = spotify_id
    client_secret = spotify_secret
    
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    results = sp.search(q=query, type='album')
    
    if results['albums']['items']:
        first_link = results['albums']['items'][0]['external_urls']['spotify']
        return first_link
    return None