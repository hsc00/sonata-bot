"""Tests for core utility functions."""

import pytest

from bot.core.constants import FULL_STAR, HALF_STAR
from bot.core.utils import (
    score_to_stars,
)


class TestScoreToStars:
    """Tests for the score_to_stars function."""

    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (1, HALF_STAR),
            (2, FULL_STAR),
            (3, FULL_STAR + HALF_STAR),
            (4, FULL_STAR * 2),
            (5, FULL_STAR * 2 + HALF_STAR),
            (6, FULL_STAR * 3),
            (7, FULL_STAR * 3 + HALF_STAR),
            (8, FULL_STAR * 4),
            (9, FULL_STAR * 4 + HALF_STAR),
            (10, FULL_STAR * 5),
        ],
    )
    def test_valid_scores_return_correct_stars(self, score: int, expected: str) -> None:
        """Test that valid scores (1-10) return correct star combinations."""
        result = score_to_stars(score)
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_score",
        [0, 11, -5, -1, 100],
    )
    def test_invalid_scores_raise_value_error(self, invalid_score: int) -> None:
        """Test that invalid scores raise ValueError."""
        with pytest.raises(ValueError, match="Score must be between 1 and 10"):
            score_to_stars(invalid_score)
