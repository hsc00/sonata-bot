import requests

def get_sampled_song_titles(track_name, artist_name, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    search_url = "https://api.genius.com/search"
    search_params = {"q": f"{track_name} {artist_name}"}

    # Lookup no API da Genius
    response = requests.get(search_url, headers=headers, params=search_params)

    if response.status_code != 200:
        print(f"Request failed with status code: {response.status_code}")
        return {}

    # Extrair o ID da musica
    song_id = extract_song_id(response.json())

    if song_id is None:
        print("Song not found in search results.")
        return {}

     # API call com o ID da musica
    song_url = f"https://api.genius.com/songs/{song_id}"
    song_response = requests.get(song_url, headers=headers)

    if song_response.status_code != 200:
        print(f"Failed to retrieve song details, status code: {song_response.status_code}")
        return {}

    # Limpeza da resposta do API (isto e bueda lento porque o API devolve mais de 2000 linhas de info)
    return extract_related_titles(song_response.json())

def extract_song_id(search_results):
    try:
        return search_results["response"]["hits"][0]["result"]["id"]
    except (IndexError, KeyError):
        return None

def extract_related_titles(song_data):
    # Dicionario fixe para organizar isto melhor (por tipo de relaçao)
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

    # Tirar as listas vazias do dicionario
    return {k: v for k, v in related_titles.items() if v}

# Exemplo bueda fixe
access_token = 'mrA06wr4necgep89aHVy1Om5g1kx4QLf0marSNvZo0AFrZmtmHQJ5b5yODtRpTYD'  
track_name = "The Story of OJ"
artist_name = "Jay Z"

related_titles = get_sampled_song_titles(track_name, artist_name, access_token)

if related_titles:
    print("Related Songs Found:")
    for relationship, titles in related_titles.items():
        print(f"{relationship}:")
        for title in titles:
            print(f"  - {title}")
else:
    print("No related songs found.")