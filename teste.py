import requests

def clean_wiki_text(text):
    # Add your cleaning logic here
    return text

def get_album_info_from_lastfm(artist_name, album_name, lastfm_api_key):
    lastfm_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={lastfm_api_key}&artist={artist_name}&album={album_name}&format=json"
    lastfm_response = requests.get(lastfm_url)
    lastfm_data = lastfm_response.json()
    album_cover_url = lastfm_data['album']['image'][-1]['#text'] if 'album' in lastfm_data and 'image' in lastfm_data['album'] else None
    album_wiki = clean_wiki_text(lastfm_data['album']['wiki']['content']) if 'album' in lastfm_data and 'wiki' in lastfm_data['album'] else None
    
    if album_wiki:
        read_more_link_start = album_wiki.rfind("[Read more](")
        read_more_link = album_wiki[read_more_link_start:] if read_more_link_start != -1 else ''
        max_length = 1200 - len(read_more_link)
        if len(album_wiki) > max_length:
            album_wiki = album_wiki[:max_length-3] + '...' + read_more_link
        elif read_more_link and not album_wiki.endswith(read_more_link):
            album_wiki = album_wiki + read_more_link
    
    return album_cover_url, album_wiki

# Example usage:
artist_name = "The Beatles"
album_name = "Abbey Road"
lastfm_api_key = "your_lastfm_api_key"

album_cover_url, album_wiki = get_album_info_from_lastfm(artist_name, album_name, lastfm_api_key)
print(album_cover_url)
print(album_wiki)
