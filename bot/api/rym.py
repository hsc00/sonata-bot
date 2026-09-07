from __future__ import annotations

import logging

from api.google_search import search_google_general_async

logger = logging.getLogger(__name__)

RYM_PROFILE_PATTERN = r"https?://(?:www\.)?rateyourmusic\.com/~([^/?#]+)"


async def fetch_rym_user_info(username: str) -> dict | None:
    results = await search_google_general_async(f"site:rateyourmusic.com/~{username}")

    if not results:
        logger.warning("No Google result for RYM user %s", username)
        return None

    for result in results:
        link = result.get("link", "")
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        thumbnail = result.get("thumbnail")

        if "rateyourmusic.com/~" not in link:
            continue

        return {
            "username": username,
            "url": link,
            "title": title,
            "snippet": snippet,
            "thumbnail": thumbnail,
        }

    logger.warning(
        "No matching RYM profile found for %s in %d results", username, len(results)
    )
    return None
