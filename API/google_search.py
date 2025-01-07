import requests
import logging 

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
