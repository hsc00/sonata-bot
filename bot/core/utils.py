from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote, unquote, urlparse

import discord  # noqa: TC002
from api.google_search import search_google, search_google_async
from api.last_fm import get_last_played
from core.constants import FULL_STAR, HALF_STAR, RATING_SCORE_MAX, RATING_SCORE_MIN
from core.errors import NoLastFMUsernameError, SonataError
from core.rating_history import maybe_schedule_refresh
from database import Album, AlbumIndex, UserInfo


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{unquote(parsed.path).rstrip('/')}"


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


def format_timestamp(value: object) -> str:
    if value is None:
        return "Unknown"

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")

    text = str(value)

    if len(text) >= 10:
        return text[:10]

    return text


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


async def fetch_album(
    user_id: str | None,
    query: str | None,
    release_url: str | None = None,
) -> Album | None:
    album_name, artist_name = await _resolve_album_query(user_id, query)
    album = await _fetch_or_create_album(album_name, artist_name, release_url)
    if album is None:
        return None
    album = _update_missing_album_details(album, album_name, artist_name)
    needs_refresh = await maybe_schedule_refresh(album)
    if not needs_refresh:
        album.last_rating_refresh = datetime.now(timezone.utc)
        album.save()
    return album


async def _resolve_album_query(
    user_id: str | None, query: str | None
) -> tuple[str, str]:
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

        return last_played[0], last_played[1]

    return query, ""


async def _fetch_or_create_album(
    album_name: str,
    artist_name: str,
    release_url: str | None = None,
) -> Album | None:
    if release_url:
        normalized_url = _normalize_url(release_url)
        non_null = False
        for candidate in Album.select().where(Album.url.is_null(non_null)):
            if _normalize_url(str(candidate.url)) == normalized_url:
                return candidate

    album = search_album(album_name, artist_name)

    if not album:
        result = await search_google_async(f"{artist_name} - {album_name}")

        if result is None:
            return None

        album = search_album(
            result["pagemap"]["musicalbum"][0]["name"],
            result["pagemap"]["musicgroup"][0]["name"],
        )

        if not album:
            album = album_from_google_result(result)
            album.last_rating_refresh = datetime.now(timezone.utc)
            album.save()
            store_album(album)
        elif not _album_matches_query(album, album_name, artist_name):
            return None

    return album


def _album_matches_query(
    album: Album,
    album_name: str,
    artist_name: str,
) -> bool:
    query_text = f"{artist_name} {album_name}".strip().lower()
    query_tokens = query_text.split()
    title_tokens = album.title.lower().split()
    artist_tokens = album.artist.lower().split()

    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
    }
    significant_query = [t for t in query_tokens if t not in stopwords]
    significant_title = [t for t in title_tokens if t not in stopwords]
    significant_artist = [t for t in artist_tokens if t not in stopwords]

    query_numbers = {t for t in significant_query if t.isdigit()}
    title_numbers = {t for t in significant_title if t.isdigit()}
    artist_numbers = {t for t in significant_artist if t.isdigit()}

    if query_numbers:
        all_result_numbers = title_numbers | artist_numbers
        if not query_numbers.intersection(all_result_numbers):
            return False

    matched_tokens = {
        t
        for t in significant_query
        if t in significant_title or t in significant_artist
    }

    match_ratio = len(matched_tokens) / len(significant_query)

    if match_ratio < 0.7:
        return False

    return not (artist_name and album.artist.lower() != artist_name.lower())


def _update_missing_album_details(
    album: Album, album_name: str, artist_name: str
) -> Album:
    logger = logging.getLogger(__name__)

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


def _finalize_album(album: Album) -> Album:
    if album.last_rating_refresh is None:
        album.last_rating_refresh = datetime.now(timezone.utc)
        album.save()

    return album


def album_from_google_result(result: dict) -> Album | None:
    """Create an Album object from a Google search result."""
    pagemap = result.get("pagemap", {})

    musicalbum = pagemap.get("musicalbum", [])
    musicgroup = pagemap.get("musicgroup", [])
    metatags = pagemap.get("metatags", [])

    if not musicalbum or not musicgroup or not metatags:
        return None

    title = musicalbum[0].get("name")
    artist = musicgroup[0].get("name")

    if not title or not artist:
        return None

    release_year_match = re.search(
        r"Released .*? (\d{4})",
        metatags[0].get("og:description", ""),
    )

    release_year = int(release_year_match.group(1)) if release_year_match else None

    if "cse_image" in pagemap:
        cover_url = f"{pagemap['cse_image'][0]['src']}/cover.jpg"

    elif "og:image" in metatags[0]:
        cover_url = f"{metatags[0]['og:image']}/cover.jpg"

    else:
        cover_url = None

    genres = (
        match := re.search(r"Genres: (.*?)\.", metatags[0].get("og:description", ""))
    ) and match.group(1)

    rating = pagemap.get("aggregaterating", [None])[0]

    if rating is not None:
        rating_score, rating_count = (
            float(rating["ratingvalue"]),
            int(rating["ratingcount"]),
        )

    else:
        rating_score, rating_count = None, None

    if matches := re.search(
        r"Rated #(\d+) in the best albums of \d+(?:, and #(\d+) of all time)?",
        metatags[0].get("og:description", ""),
    ):
        year_position, overall_position = (
            int(x) if x else None for x in matches.groups()
        )

    else:
        year_position, overall_position = None, None

    url = result.get("link", "")

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
