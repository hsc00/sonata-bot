from __future__ import annotations

import logging
import re
from urllib.parse import quote

import aiohttp
import requests
from core.config import cse_id, google_token

logger = logging.getLogger(__name__)


async def search_google_async(query: str) -> dict | None:
    """Search for a RYM album on Google asynchronously."""
    url = f"https://www.googleapis.com/customsearch/v1?q={quote(query)}&key={google_token}&cx={cse_id}"
    release_pattern = re.compile(
        r"^https:\/\/rateyourmusic.com\/release\/(album|mixtape|ep|single|musicvideo|comp|unauth|video|additional)\/([^\/]*)\/([^\/]*)\/?$",
    )

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response,
        ):
            if response.status == 200:
                results = (await response.json()).get("items", None)

                for result in results:
                    if release_pattern.match(result["link"]):
                        return result

            else:
                logger.error(
                    f"Google search failed with status code: {response.status}",
                )

                return None

    except Exception:
        logger.exception("Failed to search for album")

        return None


def search_google(query: str) -> dict | None:
    """Search for a RYM album on Google."""
    with requests.Session() as session:
        try:
            token = google_token
            search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={token}&cx={cse_id}"
            release_pattern = re.compile(
                r"^https:\/\/rateyourmusic.com\/release\/(album|mixtape|ep|single|musicvideo|comp|unauth|video|additional)\/([^\/]*)\/([^\/]*)\/?$",
            )
            response = session.get(search_url, timeout=10)

            if response.status_code == 200:
                results = response.json().get("items", None)

                for result in results:
                    # Check if the link is a RYM release
                    if release_pattern.match(result["link"]):
                        return result

            else:
                logger.error(
                    f"Google search failed with status code: {response.status_code}",
                )

                return None

        except Exception:
            logger.exception("Failed to search for album")

            return None
