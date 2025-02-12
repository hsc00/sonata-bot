import requests
from config import genius_api_key

def get_track_info(track_name):
    headers = {"Authorization": f"Bearer {genius_api_key}"}
    search_url = "https://api.genius.com/search"
    search_params = {"q": f"{track_name}"}

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

    song_data = song_response.json()

    # Extract the required information
    cover_url = song_data.get("response", {}).get("song", {}).get("song_art_image_url", "")
    credits = extract_credits(song_data)
    wiki = extract_wiki(song_data)
    links = extract_links(song_data)
    genius_url = song_data.get("response", {}).get("song", {}).get("url", "")
    artist_name = song_data.get("response", {}).get("song", {}).get("primary_artist", {}).get("name", "")
    track_name = song_data.get("response", {}).get("song", {}).get("title", "")
    release_year = song_data.get("response", {}).get("song", {}).get("release_date", "")[:4]

    return {
        "artist_name": artist_name,
        "track_name": track_name,
        "release_year": release_year,
        "cover_url": cover_url,
        "credits": credits,
        "wiki": wiki,
        "links": links,
        "genius_url": genius_url
    }

def get_track_samples(track_name):
    song_data = get_song_data(track_name)
    if not song_data:
        return {}

    return {
        "samples": extract_related_titles(song_data, "samples"),
        "sampled_in": extract_related_titles(song_data, "sampled_in")
    }

def get_track_interpolations(track_name):
    song_data = get_song_data(track_name)
    if not song_data:
        return {}

    return {
        "interpolates": extract_related_titles(song_data, "interpolates"),
        "interpolated_by": extract_related_titles(song_data, "interpolated_by")
    }

def get_track_covers(track_name):
    song_data = get_song_data(track_name)
    if not song_data:
        return {}

    return {
        "cover_of": extract_related_titles(song_data, "cover_of"),
        "covered_by": extract_related_titles(song_data, "covered_by")
    }

def get_track_remixes(track_name):
    song_data = get_song_data(track_name)
    if not song_data:
        return {}

    return {
        "remix_of": extract_related_titles(song_data, "remix_of"),
        "remixed_by": extract_related_titles(song_data, "remixed_by")
    }

def get_track_lives(track_name):
    song_data = get_song_data(track_name)
    if not song_data:
        return {}

    return {
        "live_version_of": extract_related_titles(song_data, "live_version_of"),
        "performed_live_as": extract_related_titles(song_data, "performed_live_as")
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

    return song_response.json()

def extract_song_id(search_results):
    try:
        return search_results["response"]["hits"][0]["result"]["id"]
    except (IndexError, KeyError):
        return None

def extract_related_titles(song_data, relationship_type):
    related_titles = []
    relationships = song_data.get("response", {}).get("song", {}).get("song_relationships", [])
    for relationship in relationships:
        if relationship.get("relationship_type") == relationship_type:
            for related_song in relationship.get("songs", []):
                full_title = related_song.get("full_title")
                if full_title:
                    related_titles.append(f"[{full_title}]({related_song.get('url', '')})")
    return related_titles

def extract_credits(song_data):
    credits_dict = {}
    for instrument_data in song_data.get("response", {}).get("song", {}).get("custom_performances", []):
        instrument = instrument_data.get("label")
        for artist in instrument_data.get("artists", []):
            artist_name = artist.get('name')
            genius_url = artist.get("url")
            if artist_name not in credits_dict:
                credits_dict[artist_name] = {"instruments": [], "url": genius_url}
            credits_dict[artist_name]["instruments"].append(instrument)
    
    credits = []
    for artist_name, data in credits_dict.items():
        instruments = ", ".join(data["instruments"])
        credits.append(f"[{artist_name}]({data['url']}) ({instruments})")
    
    return '\n'.join(credits)

def extract_wiki(song_data):
    print()
    genius_url = 'https://genius.com' + song_data.get("response", {}).get("song", {}).get("api_path", {})
    description_dom = song_data.get("response", {}).get("song", {}).get("description", {}).get("dom", {})
    wiki = parse_description_children(description_dom.get("children", []))

    if len(wiki) > 1200:
        truncated_wiki = wiki[:1200]
        last_period_index = truncated_wiki.rfind('.')
        if last_period_index != -1:
            truncated_wiki = truncated_wiki[:last_period_index + 1]
        else:
            truncated_wiki = truncated_wiki.rstrip()
        wiki = truncated_wiki + f".. [Read more]({genius_url})"
    
    return wiki

def parse_description_children(children):
    wiki = ""
    for child in children:
        if isinstance(child, str):
            wiki += child
        elif isinstance(child, dict) and child.get("tag") == "a":
            href = child.get("attributes", {}).get("href", "")
            link_text = "".join(parse_description_children(child.get("children", [])))
            wiki += f"[{link_text}]({href})"
        elif isinstance(child, dict):
            wiki += parse_description_children(child.get("children", []))
            if child.get("tag") == "p":
                wiki += "\n\n"
    return wiki.strip()

def extract_links(song_data):
    links = []
    for media in song_data.get("response", {}).get("song", {}).get("media", []):
        if media.get("url"):
            links.append(media.get("url"))
    return links
