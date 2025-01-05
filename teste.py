import requests
from bs4 import BeautifulSoup

def get_streaming_links(artist, album, year):
    query = f"{artist} {album} {year} streaming"
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    streaming_links = []
    for div in soup.find_all('div', {'data-attrid': 'action:listen_album'}):
        for a in div.find_all('a', href=True):
            streaming_links.append(a['href'])

    return streaming_links

# Example usage
artist_name = "Joy Division"
album_name = "Closer"
release_year = "1980"
links = get_streaming_links(artist_name, album_name, release_year)
print(links)
