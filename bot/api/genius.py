from __future__ import annotations

import json

from core.config import genius_api_key
from lyricsgenius import Genius

genius = Genius(genius_api_key)


def get_track_relationships(track_name: str) -> dict | None:
    song = genius.search_song(track_name)

    if not song:
        return None

    song_json = song.to_json()

    if not song_json:
        return None

    json_data = json.loads(song_json)
    relationships = json_data.get("song_relationships", [])

    return {
        "artist_name": json_data["artist_names"],
        "track_name": json_data["title"],
        "cover_url": json_data["song_art_image_url"],
        "url": json_data["url"],
        "relationships": {x["relationship_type"]: x["songs"] for x in relationships},
    }
