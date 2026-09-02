from __future__ import annotations

import logging
import re
from urllib.parse import quote

import discord  # noqa: TC002
from api.google_search import search_google
from api.last_fm import get_last_played
from core.constants import FULL_STAR, HALF_STAR, RATING_SCORE_MAX, RATING_SCORE_MIN
from core.errors import NoLastFMUsernameError, SonataError
from database import Album, AlbumIndex, UserInfo


def get_user_display_names(guild: discord.Guild, user_ids: set[str]) -> dict[str, str]:
    """Resolve Discord display names for a set of user IDs in a guild."""
    display_names: dict[str, str] = {}

    for member in guild.members:
        if str(member.id) in user_ids:
            display_names[str(member.id)] = member.display_name

    return display_names


def score_to_stars(score: int) -> str:
    if not (RATING_SCORE_MIN <= score <= RATING_SCORE_MAX):
        message = f"Score must be between {RATING_SCORE_MIN} and {RATING_SCORE_MAX}"
        raise ValueError(message)

    normalized_score = score / 2
    full_stars = int(normalized_score)
    half_star = HALF_STAR if normalized_score - full_stars >= 0.5 else ""

    return FULL_STAR * full_stars + half_star


def store_album(album: Album) -> None:
    (
        AlbumIndex.insert(
            {
                AlbumIndex.rowid: album.id,
                AlbumIndex.title: album.title,
                AlbumIndex.artist: album.artist,
            },
        )
        .on_conflict_ignore()
        .execute()
    )


def search_album(album_name: str, artist_name: str = "") -> Album | None:
    match = f"title:{album_name}"

    if artist_name:
        match += f" artist:{artist_name}"

    query = (
        AlbumIndex.select(Album)
        .join(Album, on=(Album.id == AlbumIndex.rowid))
        .where(AlbumIndex.match(match))
        .order_by(AlbumIndex.bm25())
    )

    return query.first().album if query.exists() else None


async def fetch_album(user_id: str | None, query: str | None) -> Album | None:
    logger = logging.getLogger(__name__)

    # Get last played album if no query is provided
    if query is None:
        user = UserInfo.get_or_none(UserInfo.user_id == user_id)
        last_fm_username = user.lastfm_username if user else None

        if last_fm_username is None:
            raise NoLastFMUsernameError

        last_played = get_last_played(last_fm_username)

        if not last_played:
            raise SonataError(
                "❌ Could not retrieve the last played album. Please provide a search term.",
            )

        album_name, artist_name, _ = last_played

    else:
        album_name, artist_name = query, ""

    # Search for the album in the database
    album = search_album(album_name, artist_name)

    # If the album is not found in the database, search for it on Google
    if not album:
        logger.info(
            f'Album "{album_name}" not found in the database. Searching on Google...',
        )

        # Search for the album on Google
        result = search_google(f"{artist_name} - {album_name}")

        if result is None:
            logger.info(
                f'❌ No results found for "{artist_name} - {album_name}".',
            )

            return None

        # Search again with the result name
        album = search_album(
            result["pagemap"]["musicalbum"][0]["name"],
            result["pagemap"]["musicgroup"][0]["name"],
        )

        if not album:
            album = album_from_google_result(result)

    # Update album details if they are missing
    if album.rating_count is None:
        logger.info(f'Album "{album_name}" found, but missing details. Updating...')
        result = search_google(
            f"{album_name}" if not artist_name else f"{artist_name} - {album_name}",
        )

        if result:
            updated_album = album_from_google_result(result)

            for field in [
                "release_year",
                "cover_url",
                "genres",
                "rating_score",
                "rating_count",
                "year_position",
                "overall_position",
                "url",
            ]:
                setattr(album, field, getattr(updated_album, field))

            album.save()

    return album


def album_from_google_result(result: dict) -> Album:
    """Create an Album object from a Google search result."""
    pagemap = result["pagemap"]

    title = pagemap["musicalbum"][0]["name"]
    artist = pagemap["musicgroup"][0]["name"]

    release_year_match = re.search(
        r"Released .*? (\d{4})",
        pagemap["metatags"][0]["og:description"],
    )

    release_year = int(release_year_match.group(1)) if release_year_match else None

    if "cse_image" in pagemap:
        cover_url = f"{pagemap['cse_image'][0]['src']}/cover.jpg"

    elif "og:image" in pagemap["metatags"][0]:
        cover_url = f"{pagemap['metatags'][0]['og:image']}/cover.jpg"

    else:
        cover_url = None

    genres = (
        match := re.search(r"Genres: (.*?)\.", pagemap["metatags"][0]["og:description"])
    ) and match.group(1)

    rating = pagemap.get("aggregaterating", [None])[0]

    if rating is not None:
        rating_score, rating_count = (
            float(rating["ratingvalue"]),
            int(
                rating["ratingcount"],
            ),
        )

    else:
        rating_score, rating_count = None, None

    if matches := re.search(
        r"Rated #(\d+) in the best albums of \d+(?:, and #(\d+) of all time)?",
        pagemap["metatags"][0]["og:description"],
    ):
        year_position, overall_position = (
            int(x) if x else None for x in matches.groups()
        )

    else:
        year_position, overall_position = None, None

    url = result["link"]

    return Album(
        title=title,
        artist=artist,
        album_artist=artist,
        release_year=release_year,
        cover_url=cover_url,
        genres=genres,
        rating_score=rating_score,
        rating_count=rating_count,
        year_position=year_position,
        overall_position=overall_position,
        url=url,
    )


def create_rym_search_artist_url(artist_name: str) -> str:
    """Create a RateYourMusic search URL for the given artist name."""
    return (
        f"https://rateyourmusic.com/search?searchtype=a&searchterm={quote(artist_name)}"
    )


def create_rym_search_release_url(release_name: str) -> str:
    """Create a RateYourMusic search URL for the given release name."""
    return f"https://rateyourmusic.com/search?searchtype=l&searchterm={quote(release_name)}"


def create_rym_user_url(username: str) -> str:
    """Create a RateYourMusic user profile URL."""
    return f"https://rateyourmusic.com/~{quote(username)}"
