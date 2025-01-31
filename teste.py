import requests

API_KEY = 'v4cikhgpSAV0ZIDqvcizvqSgPikw6kPdd7WB'
BASE_URL = 'https://api.setlist.fm/rest/1.0'
ARTIST_NAME = 'charli xcx'  # Replace with the artist's name

headers = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}

# Search for the artist by name
search_response = requests.get(f'{BASE_URL}/search/artists?artistName={ARTIST_NAME}', headers=headers)

if search_response.status_code == 200:
    search_data = search_response.json()
    if 'artist' in search_data and search_data['artist']:
        # Find the artist with the exact name match
        artist = next((a for a in search_data['artist'] if a['name'].lower() == ARTIST_NAME.lower()), None)
        if artist:
            artist_mbid = artist['mbid']

            # Now, get the last setlist for the artist using their MusicBrainz ID
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

                    print(f'Concert Name: {concert_name}, {city_name}, {country_name}')
                    print(last_setlist['url'])
                    print(f'Date: {concert_date}')
                    print('Tracks Played:')
                    for set_ in sets:
                        if 'song' in set_:
                            for track in set_['song']:
                                print(f" - {track['name']}")

                else:
                    print('No setlists found for the artist.')
            else:
                print('Failed to retrieve setlists:', setlist_response.status_code, setlist_response.text)
        else:
            print('Artist not found.')
    else:
        print('Artist not found.')
else:
    print('Failed to search for artist:', search_response.status_code, search_response.text)
