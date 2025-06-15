from math import ceil
from typing import Self, Optional

import discord

import utils
from database import Album, Rating
from utils import score_to_stars, RYM_RATING_COLORS
from utils.views import PaginatorView


class EmbedBuilder:
    def __init__(self):
        self.title: Optional[str] = None
        self.description: Optional[str] = None
        self.url: Optional[str] = None
        self.thumbnail: Optional[str] = None
        self.author: Optional[tuple[str, str]] = None
        self.footer: Optional[str] = None
        self.color: discord.Color = discord.Color.blue()

    def reset(self) -> Self:
        self.__init__()

        return self

    def with_title(self, title: str) -> Self:
        self.title = title

        return self

    def with_description(self, description: str) -> Self:
        self.description = description

        return self

    def with_url(self, url: str) -> Self:
        self.url = url

        return self

    def with_thumbnail(self, thumbnail: str) -> Self:
        self.thumbnail = thumbnail

        return self

    def with_author(self, name: str, icon_url: str) -> Self:
        self.author = (name, icon_url)

        return self

    def with_color(self, color: discord.Color) -> Self:
        self.color = color

        return self

    def with_footer(self, text: str) -> Self:
        self.footer = text

        return self

    def build(self) -> discord.Embed:
        if not self.title or not self.description:
            raise ValueError("Title and description must be set before building the embed.")

        embed = discord.Embed(
            title=self.title,
            description=self.description,
            url=self.url,
            color=self.color
        )

        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)

        if self.author:
            name, icon_url = self.author
            embed.set_author(name=name, icon_url=icon_url)

        if self.url:
            embed.url = self.url

        if self.footer:
            embed.set_footer(text=self.footer)

        return embed


def format_album_title(album: Album) -> str:
    return f"{album.artist} - {album.title} ({album.release_year})"


def format_star_score(score: float) -> str:
    return f"**{(score / 2):.2f}** ⭐"


def make_album_embed(album: Album) -> discord.Embed:
    """
    Create an embed for the album.
    """

    title = format_album_title(album)

    description = (
        f"*{album.genres}*\n\n"
        f"{format_star_score(album.rating_score * 2)} from **{album.rating_count:,d}** ratings\n"
    )

    if album.year_position:
        description += f"**#{album.year_position}** of [{album.release_year}](https://rateyourmusic.com/charts/top/album/{album.release_year}/)"

    if album.overall_position:
        description += f", **#{album.overall_position}** [overall](https://rateyourmusic.com/charts/top/album/all-time/)\n\n"

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_url(album.url)
        .with_thumbnail(album.cover_url)
        .build()
    )


def make_who_rated_album_embed(
        album: Album, ratings: list[Rating], user_id: int, server_name: str
) -> discord.Embed:
    """
    Create an embed for the album ratings.
    """

    average_score = (sum(rating.score for rating in ratings) / len(ratings)) / 2

    title = format_album_title(album)
    description = f"**{average_score:.2f}** ⭐ in **{server_name}** from **{len(ratings):,d}** ratings\n\n"

    for (i, rating) in enumerate(ratings, start=1):
        position = f"{i}."

        if rating.user == str(user_id):
            position = f"**{position}**"

        description += f"{position} <@{rating.user}> - **{rating.score / 2:.1f}** ⭐\n"

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_url(album.url)
        .with_thumbnail(album.cover_url)
        .build()
    )


def make_best_rated_albums_embed(
        top_releases: list[tuple[Album, int, int]],
        server_name: str,
        start: int = 1
) -> discord.Embed:
    """
    Create an embed for the album ratings.
    """

    lines = []

    for i, (album, average_score, rating_count) in enumerate(top_releases, start=start):
        lines.append(
            f"{i}. {album.artist} - {album.title} (**{(average_score / 2):.2f}** ⭐)"
        )

    title = f"Best rated albums in {server_name}"
    description = "\n".join(lines)

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .build()
    )


def make_album_of_the_year_embed(
        ratings: list[Rating],
        user: discord.user.User,
        year: int,
        start: int = 1
) -> discord.Embed:
    """
    Create an embed for the album ratings.
    """

    lines = []

    for i, rating in enumerate(ratings[:10], start=start):
        lines.append(
            f"{i}. {rating.album.artist} - {rating.album.title} \\- **{(rating.score / 2):.2f}** ⭐"
        )

    title = f"Top {year} releases for {user.display_name}"
    description = "\n".join(lines)

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_thumbnail(ratings[0].album.cover_url)
        .build()
    )


def make_rating_embed(
        user: discord.user.User,
        rating: Rating
) -> discord.Embed:
    """
    Create an embed for the rating.
    """

    album = rating.album

    title = f"{album.artist} - {album.title} ({album.release_year})"
    description = f"{score_to_stars(rating.score)}\n\n"

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_url(album.url)
        .with_thumbnail(album.cover_url)
        .with_author(f"{user.name} rated...", user.avatar.url)
        .with_color(discord.Color(int(RYM_RATING_COLORS[rating.score].lstrip('#'), 16)))
        .build()
    )


def make_artist_ratings_embed(ratings: list[Rating], artist: str, user: discord.User) -> discord.Embed:
    lines = []

    for i, rating in enumerate(ratings[:10], start=1):
        lines.append(
            f"{i}. {rating.album.title} \\- **{(rating.score / 2):.2f}** ⭐"
        )

    title = f"Top {artist} albums for {user.display_name}"

    description = f"Average score: **{(sum(rating.score for rating in ratings) / len(ratings) / 2):.2f}** ⭐\n\n"
    description += "\n".join(lines)

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .build()
    )


def make_ratinks_rank_embed(server_name: str, ratings: list[Rating], start=1) -> discord.Embed:
    lines = []

    for i, row in enumerate(ratings, start=start):
        lines.append(f"{i}. <@{row.user}> ({row.rating_count})")

    title = f"{server_name} Ratings Rank"
    description = "\n".join(lines)

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .build()
    )


def make_ratings_rank_view(server_name: str, ratings: list[Rating]) -> PaginatorView:
    pages = []
    num_pages = ceil(len(ratings) / 10)

    for i in range(num_pages):
        page_ratings = ratings[i * 10:(i + 1) * 10]
        page = make_ratinks_rank_embed(server_name, page_ratings, start=i)
        page.set_footer(text=f"Page {i + 1}/{num_pages}")

        pages.append(page)

    return PaginatorView(pages)


def make_most_rated_releases_embed(albums, start: int = 1) -> discord.Embed:
    """
    Create an embed for the most rated releases.
    """

    description = "\n".join(
        f"{i}. {row.artist} \\- {row.title} (**{row.rating_count}** ratings)"
        for i, row in enumerate(albums, start=start)
    )

    return (
        EmbedBuilder()
        .with_title("Releases with most ratings")
        .with_description(description)
        .build()
    )


def make_best_rated_artists_embed(server_name: str, best_rated_artists) -> discord.Embed:
    """
    Create an embed for the best rated artists.
    """

    title = f"Best rated artists in {server_name}"
    description = "\n".join(
        f"{i}. {row.artist} (**{row.average_score / 2:.2f} ⭐** from **{row.releases_count}** releases)"
        for i, row in enumerate(best_rated_artists, start=1)
    )

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .build()
    )
