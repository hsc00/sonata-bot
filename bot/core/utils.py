import logging
import re

from urllib.parse import quote

from database import Album
from typing import Optional, Callable

from core.constants import FULL_STAR, HALF_STAR
from core.errors import SonataError
from core.views import PaginatorView

from database import AlbumIndex, UserInfo

from api.last_fm import get_last_played
from api.google_search import search_google

def score_to_stars(score: int) -> str:
    if not (1 <= score <= 10):
        raise ValueError("Score must be between 1 and 10")

    normalized_score = score / 2
    full_stars = int(normalized_score)
    half_star = HALF_STAR if normalized_score - full_stars >= 0.5 else ""

    return FULL_STAR * full_stars + half_star


def store_album(album: Album) -> None:
    (AlbumIndex.insert(
        {
            AlbumIndex.rowid: album.id,
            AlbumIndex.title: album.title,
            AlbumIndex.artist: album.artist,
        }
    )
     .on_conflict_ignore()
     .execute())


def search_album(album_name: str, artist_name: str = "") -> Album:
    query = f'{album_name} {artist_name}'.strip()

    return (
        Album.select()
        .join(AlbumIndex, on=(Album.id == AlbumIndex.rowid))
        .where(AlbumIndex.match(query))
        .order_by(AlbumIndex.bm25())
        .first()
    )


async def fetch_album(user_id: str | None, query: str) -> Optional[Album]:
    logger = logging.getLogger(__name__)

    # Get last played album if no query is provided
    if query is None:
        user = UserInfo.get_or_none(
            UserInfo.user_id == user_id,
        )

        if user is None:
            raise SonataError(
                "❌ No last.fm username set. Please provide a search term or set your last.fm username."
            )

        last_fm_username = user.lastfm_username
        last_played = get_last_played(last_fm_username)

        if not last_played:
            raise SonataError(
                "❌ Could not retrieve the last played album. Please provide a search term."
            )

        album_name, artist_name, _ = last_played

    else:
        album_name, artist_name = query, ""

    # Search for the album in the database
    album = search_album(album_name, artist_name)

    # If the album is not found in the database, search for it on Google
    if not album:
        logger.info(
            f'Album "{album_name}" not found in the database. Searching on Google...'
        )

        # Search for the album on Google
        result = search_google(album_name)

        if result is None:
            raise SonataError(
                f'❌ No results found for "{query}".'
            )

        # Search again with the result name
        album = search_album(result["pagemap"]["musicalbum"][0]["name"])

        if not album:
            album = album_from_google_result(result)

    # Update album details if they are missing
    if album.rating_count is None:
        logger.info(f'Album "{album_name}" found, but missing details. Updating...')
        result = search_google(album_name)

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
    """
    Create an Album object from a Google search result.
    """

    pagemap = result["pagemap"]

    title = pagemap["musicalbum"][0]["name"]
    artist = pagemap["musicgroup"][0]["name"]

    release_year = int(
        re.search(
            r"Released .* (\d{4})", pagemap["metatags"][0]["og:description"]
        ).group(1)
    )

    cover_url = pagemap["cse_thumbnail"][0]["src"]

    genres = (match := re.search(r"Genres: (.*?)\.", pagemap["metatags"][0]["og:description"])) and match.group(1)

    rating = pagemap.get("aggregaterating", [None])[0]

    if rating is not None:
        rating_score, rating_count = float(rating["ratingvalue"]), int(
            rating["ratingcount"]
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

    album = Album(
        title=title,
        artist=artist,
        release_year=release_year,
        cover_url=cover_url,
        genres=genres,
        rating_score=rating_score,
        rating_count=rating_count,
        year_position=year_position,
        overall_position=overall_position,
        url=url,
    )

    return album


def create_rym_artist_url(artist_name: str) -> str:
    """
    Create a RateYourMusic URL for the given artist name.
    """

    return f"https://rateyourmusic.com/artist/{quote(artist_name.replace(' ', '-').lower())}"


def paginate_embeds(
        items: list,
        embed_fn: Callable,
        per_page: int = 10,
        *args,
        **kwargs
):
    pages = []
    num_pages = (len(items) + per_page - 1) // per_page

    for i in range(num_pages):
        page_items = items[i * per_page:(i + 1) * per_page]
        embed = embed_fn(page_items, *args, **kwargs, start=i * per_page)
        embed.set_footer(text=f"Page {i + 1}/{num_pages}")
        pages.append(embed)

    view = PaginatorView(pages)

    return view, pages
