from __future__ import annotations

import requests
from core.config import lastfm_api_key as api_key
from core.errors import SonataError


def get_last_played(username: str) -> tuple[str, str, str]:
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={username}&api_key={api_key}&format=json"
    response = requests.get(url, timeout=10)
    data = response.json()

    if "recenttracks" in data and "track" in data["recenttracks"]:
        last_track = data["recenttracks"]["track"][0]

        track_name = last_track["name"]
        artist_name = last_track["artist"]["#text"]
        album_name = last_track["album"]["#text"]

        return (album_name, artist_name, track_name)

    raise SonataError(
        "Could not retrieve the last played track. Please provide a search term.",
    )
