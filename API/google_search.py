import requests
import logging 
from bs4 import BeautifulSoup

def google_search(query, google_tokens, cse_id):
    for token in google_tokens:
        try:
            search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={token}&cx={cse_id}"
            response = requests.get(search_url)
            if response.status_code == 429:
                logging.warning(f"Rate limit exceeded for token {token}, retrying with next token.")
                continue
            results = response.json().get('items', [])
            if results:
                return results
        except Exception as e:
            logging.error(f"Error during Google search with token {token}: {e}")
    logging.warning('No results found')
    return None

def fetch_streaming_links(query, action):
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    streaming_links = []
    for div in soup.find_all('div', {'data-attrid': 'action:' + action}):
        for a in div.find_all('a', href=True):
            href = a['href']
            if any(service in href for service in ['spotify', 'apple', 'music.youtube', 'soundcloud', 'bandcamp']):
                streaming_links.append(href)
    return streaming_links
