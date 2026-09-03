"""Tests for core rating history functionality."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.core.rating_history import (
    _refreshing,
    _refreshing_tasks,
    maybe_schedule_refresh,
)


@pytest.mark.asyncio
async def test_maybe_schedule_refresh_schedules_when_stale() -> None:
    _refreshing.clear()
    _refreshing_tasks.clear()
    album = MagicMock()
    album.id = 1
    album.last_rating_refresh = datetime.now(timezone.utc) - timedelta(days=8)

    with (
        patch(
            "bot.core.rating_history.search_google_async",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("bot.core.rating_history.Album.get_by_id", return_value=album),
    ):
        assert await maybe_schedule_refresh(album) is True
        await asyncio.sleep(0)
        for task in _refreshing_tasks:
            await task

    assert album.last_rating_refresh is not None


@pytest.mark.asyncio
async def test_maybe_schedule_refresh_skips_when_fresh() -> None:
    _refreshing.clear()
    _refreshing_tasks.clear()
    album = MagicMock()
    album.id = 1
    album.last_rating_refresh = datetime.now(timezone.utc) - timedelta(days=1)

    with patch(
        "bot.core.rating_history.search_google_async",
        new_callable=AsyncMock,
    ) as mock_search:
        assert await maybe_schedule_refresh(album) is False
        await asyncio.sleep(0)
        mock_search.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_schedule_refresh_schedules_when_never_refreshed() -> None:
    _refreshing.clear()
    _refreshing_tasks.clear()
    album = MagicMock()
    album.id = 1
    album.last_rating_refresh = None

    with (
        patch(
            "bot.core.rating_history.search_google_async",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("bot.core.rating_history.Album.get_by_id", return_value=album),
    ):
        assert await maybe_schedule_refresh(album) is True
        await asyncio.sleep(0)
        for task in _refreshing_tasks:
            await task

    assert album.last_rating_refresh is not None


@pytest.mark.asyncio
async def test_maybe_schedule_refresh_avoids_duplicate_tasks() -> None:
    _refreshing.clear()
    _refreshing_tasks.clear()
    album = MagicMock()
    album.id = 1
    album.last_rating_refresh = datetime.now(timezone.utc) - timedelta(days=8)

    with (
        patch(
            "bot.core.rating_history.search_google_async",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("bot.core.rating_history.Album.get_by_id", return_value=album),
    ):
        await maybe_schedule_refresh(album)
        await maybe_schedule_refresh(album)
        await asyncio.sleep(0)
        assert len(_refreshing_tasks) == 1


@pytest.mark.asyncio
async def test_refresh_creates_history_when_rating_changes() -> None:
    album = MagicMock()
    album.id = 1
    album.rating_score = 3.5
    album.rating_count = 100
    album.last_rating_refresh = datetime.now(timezone.utc) - timedelta(days=8)

    mock_result = {
        "pagemap": {
            "aggregaterating": [
                {
                    "ratingvalue": "4.0",
                    "ratingcount": "200",
                }
            ],
        },
    }

    with (
        patch(
            "bot.core.rating_history.search_google_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ),
        patch("bot.core.rating_history.Album.get_by_id", return_value=album),
        patch(
            "bot.core.rating_history.RatingHistory.create",
        ) as mock_create,
    ):
        assert await maybe_schedule_refresh(album) is True
        await asyncio.sleep(0)
        for task in _refreshing_tasks:
            await task

    mock_create.assert_called_once()
    assert album.rating_score == 4.0
    assert album.rating_count == 200
    assert album.last_rating_refresh is not None


@pytest.mark.asyncio
async def test_refresh_does_not_create_history_when_rating_unchanged() -> None:
    album = MagicMock()
    album.id = 1
    album.rating_score = 3.5
    album.rating_count = 100
    album.last_rating_refresh = datetime.now(timezone.utc) - timedelta(days=8)

    mock_result = {
        "pagemap": {
            "aggregaterating": [
                {
                    "ratingvalue": "3.5",
                    "ratingcount": "200",
                }
            ],
        },
    }

    with (
        patch(
            "bot.core.rating_history.search_google_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ),
        patch("bot.core.rating_history.Album.get_by_id", return_value=album),
        patch(
            "bot.core.rating_history.RatingHistory.create",
        ) as mock_create,
    ):
        assert await maybe_schedule_refresh(album) is True
        await asyncio.sleep(0)
        for task in _refreshing_tasks:
            await task

    mock_create.assert_not_called()
    assert album.rating_score == 3.5
    assert album.rating_count == 200
    assert album.last_rating_refresh is not None
