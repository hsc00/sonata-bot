import re
import requests

from config import google_tokens, cse_id


def search_album(query: str) -> dict | None:
    """
    Search for a RYM album on Google.
    """

    with requests.Session() as session:
        try:
            token = google_tokens[0]
            search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={token}&cx={cse_id}"
            release_pattern = re.compile(
                r"^https:\/\/rateyourmusic.com\/release\/(album|mixtape|ep|single|musicvideo|comp|unauth|video|additional)\/([^\/]*)\/([^\/]*)\/?$"
            )
            response = session.get(search_url)

            if response.status_code == 200:
                results = response.json().get("items", None)

                for result in results:
                    # Check if the link is a RYM release
                    if release_pattern.match(result["link"]):
                        return result

            return None

        except Exception as e:
            print(f"Failed to search for album: {e}")

            return None
