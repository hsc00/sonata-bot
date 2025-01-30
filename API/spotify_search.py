import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# not being used for now. getting links from google
def get_spotify_links(query):
    client_id = 'a67b0bdaeebb40aabc7549142c978164'
    client_secret = 'd7d029eaab0141399342abb3ca21519f'
    
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    results = sp.search(q=query, type='album')
    
    if results['albums']['items']:
        first_link = results['albums']['items'][0]['external_urls']['spotify']
        return first_link
    return None

# Example usage
first_link = get_spotify_links("charli xcx - brat")
print(first_link)
