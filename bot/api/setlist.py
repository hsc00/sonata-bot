from __future__ import annotations

import logging

import aiohttp
from core.config import setlist_api_key as api_key

logger = logging.getLogger(__name__)

SETLIST_FM_BASE = "https://api.setlist.fm/rest/1.0"


async def _setlist_request(endpoint: str) -> dict | None:
    url = f"{SETLIST_FM_BASE}{endpoint}"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "User-Agent": "SonataBot/1.0",
    }

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers=headers,
            ) as response,
        ):
            if response.status == 200:
                return await response.json()

            logger.error(
                "setlist.fm request failed: %s %s",
                response.status,
                await response.text(),
            )

            return None

    except Exception:
        logger.exception("setlist.fm request failed for endpoint: %s", endpoint)

        return None


async def search_artist(name: str) -> dict | None:
    data = await _setlist_request(
        f"/search/artists?artistName={name}&p=1&sort=sortName"
    )

    if data and "artist" in data and data["artist"]:
        return data["artist"][0]

    return None


async def get_artist_setlists(artist_mbid: str) -> list[dict]:
    data = await _setlist_request(f"/artist/{artist_mbid}/setlists?p=1")

    if data and "setlist" in data:
        return data["setlist"]

    return []
