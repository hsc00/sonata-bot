import requests
from config import genius_api_key

def get_sampled_song_titles(track_name, artist_name):
    headers = {"Authorization": f"Bearer {genius_api_key}"}
    search_url = "https://api.genius.com/search"
    search_params = {"q": f"{track_name} {artist_name}"}

    response = requests.get(search_url, headers=headers, params=search_params)
    if response.status_code != 200:
        print(f"Request failed with status code: {response.status_code}")
        return {}
    # Get track ID
    song_id = extract_song_id(response.json())
    if song_id is None:
        print("Song not found in search results.")
        return {}
     # Get song info
    song_url = f"https://api.genius.com/songs/{song_id}"
    song_response = requests.get(song_url, headers=headers)

    if song_response.status_code != 200:
        print(f"Failed to retrieve song details, status code: {song_response.status_code}")
        return {}
    
    # API response cleanup to improve speed
    return extract_related_titles(song_response.json())

def extract_song_id(search_results):
    try:
        return search_results["response"]["hits"][0]["result"]["id"]
    except (IndexError, KeyError):
        return None

def extract_related_titles(song_data):
    related_titles = {
        "samples": [],
        "sampled_in": [],
        "interpolates": [],
        "interpolated_by": [],
        "cover_of": [],
        "covered_by": []
    }

    relationships = song_data.get("response", {}).get("song", {}).get("song_relationships", [])

    for relationship in relationships:
        rel_type = relationship.get("relationship_type")
        if rel_type in related_titles:
            for related_song in relationship.get("songs", []):
                full_title = related_song.get("full_title")
                if full_title:
                    related_titles[rel_type].append(full_title)

    # Remove empty lists from dictionary
    return {k: v for k, v in related_titles.items() if v}
