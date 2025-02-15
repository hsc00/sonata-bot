import requests
import time
from datetime import datetime

from config import setlist_api_key


base_url = 'https://api.setlist.fm/rest/1.0'
headers = {
    'Accept': 'application/json',
    'x-api-key': setlist_api_key
}

def get_artist_id(query):
    response = requests.get(f'{base_url}/search/artists', headers=headers, params={'artistName': query})
    if response.status_code != 200:
        return {'error': 'Failed to search for artist 😞'}
    
    data = response.json()
    artist = next((a for a in data.get('artist', []) if a['name'].lower() == query.lower()), None)
    if not artist:
        return {'error': 'Artist not found 😞'}
    
    time.sleep(0.7)
    return artist


def get_setlist(query):
    artist_info = get_artist_id(query)
    if not artist_info:
        return None
    
    if 'error' in artist_info:
        return artist_info

    artist_mbid = artist_info['mbid']
    url = f"{base_url}/artist/{artist_mbid}/setlists"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(response)
        return {'error': 'Failed to get setlists 😷'}
    
    data = response.json()
    if 'setlist' not in data or not data['setlist']:
        return {'error': f'No setlists found for the artist. You can be the **first** adding one [here]({data["url"]})'}
    
    # Filter setlists to only include those before today's date
    today = datetime.now().date()
    past_setlists = [
        setlist for setlist in data['setlist']
        if datetime.strptime(setlist['eventDate'], "%d-%m-%Y").date() < today
    ]
    
    if not past_setlists:
        return {'error': f'No past setlists found for the artist. You can be the **first** adding one [here]({data["url"]})'}
    
    last_setlist = past_setlists[0]
    venue = last_setlist['venue']
    tracks_played = [track['name'] for set_ in last_setlist['sets']['set'] if 'song' in set_ for track in set_['song'] if track['name']]
    
    return {
        'artist_name': artist_info['name'],
        'concert_name': venue['name'],
        'city_name': venue['city']['name'],
        'country_name': venue['city']['country']['name'],
        'concert_date': last_setlist['eventDate'],
        'tracks_played': tracks_played,
        'url': last_setlist['url']
    }


def get_setlists(query):
    artist_info = get_artist_id(query)
    if not artist_info or 'error' in artist_info:
        return artist_info if artist_info else None

    artist_mbid = artist_info['mbid']
    url = f"{base_url}/artist/{artist_mbid}/setlists"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {'error': 'Failed to get setlists 😷'}
    
    data = response.json()
    setlist_details = [
        {
            'artist_name': artist_info['name'],
            'artist_url': artist_info['url'],
            'url': setlist['url'],
            'concert_name': setlist['venue']['name'],
            'city_name': setlist['venue']['city']['name'],
            'country_name': setlist['venue']['city']['country']['name'],
            'concert_date': setlist['eventDate']
        }
        for setlist in data.get('setlist', [])[:10]
    ]
    return setlist_details if setlist_details else {'error': 'No setlists found for the artist. You can be the **first** adding one [here]({data["url"]})'}
