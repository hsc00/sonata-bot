from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from api.google_search import search_google_async
from core.constants import RATING_REFRESH_TTL_DAYS
from database.models import Album, RatingHistory

logger = logging.getLogger(__name__)

_refreshing: set[int] = set()
_refreshing_tasks: set[asyncio.Task] = set()


def _parse_refresh_timestamp(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                parsed = datetime.strptime(value, fmt)  # noqa: DTZ007
            except ValueError:
                continue
            else:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)

                return parsed

    logger.warning("Unexpected last_rating_refresh format: %r", value)
    return None


async def maybe_schedule_refresh(album: Album) -> bool:
    """
    Schedule a background rating refresh if the album's data is stale.

    Returns True if a refresh was scheduled, False otherwise.
    """
    if album.id is None:
        return False

    if album.id in _refreshing:
        return True

    now = datetime.now(timezone.utc)
    last_refresh = _parse_refresh_timestamp(album.last_rating_refresh)

    if last_refresh is not None:
        if last_refresh.tzinfo is None:
            last_refresh = last_refresh.replace(tzinfo=timezone.utc)

        if (now - last_refresh).total_seconds() < RATING_REFRESH_TTL_DAYS * 86400:
            return False

    _refreshing.add(album.id)
    task = asyncio.create_task(_refresh_album_rating(album.id))
    _refreshing_tasks.add(task)
    task.add_done_callback(
        lambda t: (_refreshing_tasks.discard(t), _refreshing.discard(album.id))
    )

    return True


async def _refresh_album_rating(album_id: int) -> None:
    try:
        album = Album.get_by_id(album_id)
    except Album.DoesNotExist:
        _refreshing.discard(album_id)
        return

    now = datetime.now(timezone.utc)
    query = f"{album.artist} - {album.title}"
    result = await search_google_async(query)

    if result is None:
        logger.warning("Failed to refresh rating for album %s", album_id)
        album.last_rating_refresh = now
        album.save()
        _refreshing.discard(album_id)
        return

    pagemap = result.get("pagemap", {})
    rating = pagemap.get("aggregaterating", [None])[0]

    if rating is None:
        album.last_rating_refresh = now
        album.save()
        _refreshing.discard(album_id)
        return

    new_score = float(rating["ratingvalue"])
    new_count = int(rating["ratingcount"])

    old_score = album.rating_score
    old_count = album.rating_count

    album.rating_score = new_score
    album.rating_count = new_count

    if old_score != new_score:
        RatingHistory.create(
            album=album,
            rating_score=new_score,
            rating_count=new_count,
            timestamp=now,
        )
        logger.info(
            "Updated rating for album %s: %s (%s) -> %s (%s)",
            album_id,
            old_score,
            old_count,
            new_score,
            new_count,
        )
    else:
        logger.debug("Rating unchanged for album %s", album_id)

    album.last_rating_refresh = now
    album.save()
    _refreshing.discard(album_id)
