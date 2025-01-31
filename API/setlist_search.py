import requests
import time

BASE_URL = 'https://api.setlist.fm/rest/1.0'

def get_artist_id(query, setlist_api_key):
    artist_name = query
    headers = {
        'Accept': 'application/json',
        'x-api-key': setlist_api_key
    }
    # Search for the artist by name
    search_response = requests.get(f'{BASE_URL}/search/artists?artistName={artist_name}', headers=headers)

    if search_response.status_code == 200:
        search_data = search_response.json()
        if 'artist' in search_data and search_data['artist']:
            # Find the artist with the exact name match
            artist = next((a for a in search_data['artist'] if a['name'].lower() == artist_name.lower()), None)
            if artist:
                # Add a delay before making the next request
                time.sleep(1)
                return artist['mbid']
            else:
                return {'error': 'Artist not found.'}
        else:
            return {'error': 'Artist not found.'}
    else:
        return {'error': 'Failed to search for artist'}
    
# Get the last setlist for the artist using their MusicBrainz ID
def get_setlist(query, setlist_api_key):
    artist_mbid = get_artist_id(query, setlist_api_key)
    headers = {
        'Accept': 'application/json',
        'x-api-key': setlist_api_key
    }
    setlist_response = requests.get(f'{BASE_URL}/artist/{artist_mbid}/setlists', headers=headers)

    if setlist_response.status_code == 200:
        setlist_data = setlist_response.json()
        if 'setlist' in setlist_data and setlist_data['setlist']:
            last_setlist = setlist_data['setlist'][0]
            venue = last_setlist['venue']
            concert_name = venue['name']
            city_name = venue['city']['name']
            country_name = venue['city']['country']['name']
            concert_date = last_setlist['eventDate']
            sets = last_setlist['sets']['set']

            tracks_played = []
            for set_ in sets:
                if 'song' in set_:
                    for track in set_['song']:
                        if track['name'] is not "":
                            tracks_played.append(track['name'])

            return {
                'concert_name': concert_name,
                'city_name': city_name,
                'country_name': country_name,
                'concert_date': concert_date,
                'tracks_played': tracks_played,
                'url': last_setlist['url']
            }

        else:
            return {'error': 'No setlists found for the artist.'}
    else:
        return {'error': f'Failed to retrieve setlists: {setlist_response.status_code} {setlist_response.text}'}


def get_setlists(query, setlist_api_key):
    return