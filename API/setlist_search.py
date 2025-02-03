import requests
import time
from datetime import datetime

base_url = 'https://api.setlist.fm/rest/1.0'

def get_artist_id(query, setlist_api_key):
    headers = {
        'Accept': 'application/json',
        'x-api-key': setlist_api_key
    }
    
    response = requests.get(f'{base_url}/search/artists', headers=headers, params={'artistName': query})
    if response.status_code != 200:
        return {'error': 'Failed to search for artist'}
    
    data = response.json()
    artist = next((a for a in data.get('artist', []) if a['name'].lower() == query.lower()), None)
    if not artist:
        return {'error': 'Artist not found.'}
    
    time.sleep(1)
    return artist


def get_setlist(query, setlist_api_key):
    artist_info = get_artist_id(query, setlist_api_key)
    if not artist_info:
        return None
    
    if 'error' in artist_info:
        return artist_info

    artist_mbid = artist_info['mbid']
    url = f"{base_url}/artist/{artist_mbid}/setlists"
    headers = {
        'Accept': 'application/json',
        'x-api-key': setlist_api_key
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(response)
        return {'error': 'Failed to retrieve setlists'}
    
    data = response.json()
    if 'setlist' not in data or not data['setlist']:
        return {'error': 'No setlists found for the artist.'}
    
    # Filter setlists to only include those before today's date
    today = datetime.now().date()
    past_setlists = [
        setlist for setlist in data['setlist']
        if datetime.strptime(setlist['eventDate'], "%d-%m-%Y").date() < today
    ]
    
    if not past_setlists:
        return {'error': 'No past setlists found for the artist.'}
    
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


def get_setlists(query, setlist_api_key):
    artist_info = get_artist_id(query, setlist_api_key)
    if not artist_info or 'error' in artist_info:
        return artist_info if artist_info else None

    artist_mbid = artist_info['mbid']
    url = f"{base_url}/artist/{artist_mbid}/setlists"
    headers = {
        'Accept': 'application/json',
        'x-api-key': setlist_api_key
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {'error': 'Failed to retrieve setlists'}
    
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
    return setlist_details if setlist_details else {'error': 'No setlists found for the artist.'}
