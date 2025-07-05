import requests


def get_track_samples(track_name):
    song_data = get_song_data(track_name)

    if not song_data:
        return {}

    return {
        "artist_name": song_data.get("details", {}).get("artist_name", ""),
        "track_name": song_data.get("details", {}).get("track_name", ""),
        "release_year": song_data.get("details", {}).get("release_year", ""),
        "genius_url": song_data.get("details", {}).get("genius_url", ""),
        "cover_url": song_data.get("details", {}).get("cover_url", ""),
        "links": extract_links(song_data.get("full_response")),
        "interpolates": extract_related_titles(song_data.get("full_response"), "interpolates"),
        "interpolated_by": extract_related_titles(song_data.get("full_response"), "interpolated_by"),
        "samples": extract_related_titles(song_data.get("full_response"), "samples"),
        "sampled_in": extract_related_titles(song_data.get("full_response"), "sampled_in")
    }


def get_song_data(track_name):
    headers = {"Authorization": f"Bearer {genius_api_key}"}
    search_url = "https://api.genius.com/search"
    search_params = {"q": f"{track_name}"}

    response = requests.get(search_url, headers=headers, params=search_params)
    if response.status_code != 200:
        print(f"Request failed with status code: {response.status_code}")
        return None

    # Get track ID
    song_id = extract_song_id(response.json())

    if song_id is None:
        print("Song not found in search results.")
        return None

    # Get song info
    song_url = f"https://api.genius.com/songs/{song_id}"
    song_response = requests.get(song_url, headers=headers)

    if song_response.status_code != 200:
        print(f"Failed to retrieve song details, status code: {song_response.status_code}")
        return None

    song_data = song_response.json()
    details = {
        "artist_name": song_data.get("response", {}).get("song", {}).get("primary_artist", {}).get("name", ""),
        "track_name": song_data.get("response", {}).get("song", {}).get("title", ""),
        "release_year": song_data.get("response", {}).get("song", {}).get("release_date", "")[:4],
        "genius_url": song_data.get("response", {}).get("song", {}).get("url", ""),
        "cover_url": song_data.get("response", {}).get("song", {}).get("song_art_image_url", "")
    }
    return {
        "details": details,
        "full_response": song_data
    }


def extract_song_id(search_results):
    try:
        return search_results["response"]["hits"][0]["result"]["id"]
    
    except (IndexError, KeyError):
        return None
