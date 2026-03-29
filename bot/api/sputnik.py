from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SPUTNIK_URL = "https://www.sputnikmusic.com/newreleases.php"


def fetch_new_releases() -> list | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(
            f"{SPUTNIK_URL}/newreleases.php", headers=headers, timeout=10
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        elements = soup.find_all("td", class_="hi")
        releases = []

        for element in elements:
            artist_data = element.find("font", color="#111111")
            album_data = element.find("font", color="#555555")

            if artist_data and album_data:
                artist_name = artist_data.find("b").get_text(strip=True)
                release_name = album_data.get_text(strip=True)

                releases.append(f"{artist_name} - {release_name}")

    except requests.RequestException:
        logger.exception("Failed to fetch new releases from Sputnikmusic")
        return None

    else:
        return releases
