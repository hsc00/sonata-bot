from __future__ import annotations

from math import ceil
from typing import Callable, Self

import discord
from core.constants import RYM_RATING_COLORS
from core.utils import (
    create_rym_search_artist_url,
    create_rym_search_release_url,
    score_to_stars,
)
from core.views import PaginatorView
from database.models import Album, Rating


class EmbedBuilder:
    def __init__(self) -> None:
        self.title: str | None = None
        self.description: str | None = None
        self.url: str | None = None
        self.thumbnail: str | None = None
        self.author: tuple[str, str] | None = None
        self.footer: str | None = None
        self.color: discord.Color = discord.Color.blue()

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
            raise ValueError(
                "Title and description must be set before building the embed.",
            )

        embed = discord.Embed(
            title=self.title,
            description=self.description,
            url=self.url,
            color=self.color,
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
    return (
        f"{album.album_artist or album.artist} - {album.title} ({album.release_year})"
        if album.release_year
        else f"{album.artist} - {album.title}"
    )


def format_star_score(score: float) -> str:
    return f"**{(score / 2):.2f}** ⭐"


def album_embed(album: Album) -> discord.Embed:
    """Create an embed for the album."""
    title = format_album_title(album)

    description = ""

    if album.genres is not None:
        description += f"*{album.genres}*\n\n"

    if album.rating_score and album.rating_count:
        description += f"{format_star_score(album.rating_score * 2)} from **{album.rating_count:,d}** ratings\n"

    if album.year_position:
        description += f"**#{album.year_position}** of [{album.release_year}](https://rateyourmusic.com/charts/top/album/{album.release_year}/)"

    if album.overall_position:
        description += f", **#{album.overall_position}** [overall](https://rateyourmusic.com/charts/top/album/all-time/)\n\n"

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description or " ")
        .with_url(album.url)
        .with_thumbnail(album.cover_url)
        .build()
    )


def who_rated_album_embed(
    ratings: list[Rating],
    album: Album,
    user_id: int,
    server_name: str,
    start: int = 1,
) -> discord.Embed:
    """Create an embed for the album ratings."""
    average_score = (sum(rating.score for rating in ratings) / len(ratings)) / 2

    title = format_album_title(album)
    description = f"**{average_score:.2f}** ⭐ in **{server_name}** from **{len(ratings):,d}** ratings\n\n"

    for i, rating in enumerate(ratings, start=start):
        position = f"{i + 1}."

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


def best_rated_albums_embed(
    top_releases: list[tuple[Album, int, int]],
    server_name: str,
    start: int = 1,
) -> discord.Embed:
    """Create an embed for the album ratings."""
    lines = []

    for i, (album, average_score, _) in enumerate(top_releases, start=start):
        lines.append(
            f"{i}. {format_artist(album.artist)} - {format_release(album)} (**{(average_score / 2):.2f}** ⭐)",
        )

    title = f"Best rated albums in {server_name}"
    description = "\n".join(lines)

    return EmbedBuilder().with_title(title).with_description(description).build()


def album_of_the_year_embed(
    ratings: list[Rating],
    user_name: str,
    year: int,
    start: int = 1,
) -> discord.Embed:
    """Create an embed for the album ratings."""
    lines = []

    for i, rating in enumerate(ratings[:10], start=start):
        lines.append(
            f"{i}. {format_artist(rating.album.album_artist or rating.album.artist)} - {format_release(rating.album)} \\- **{(rating.score / 2):.2f}** ⭐",
        )

    title = f"Top {year} releases for {user_name}"
    description = "\n".join(lines)

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_thumbnail(ratings[0].album.cover_url)
        .build()
    )


def rating_embed(user: discord.user.User, rating: Rating) -> discord.Embed:
    """Create an embed for the rating."""
    album = rating.album

    title = f"{album.artist} - {album.title} ({album.release_year})"
    description = f"{score_to_stars(rating.score)}\n\n"

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_url(album.url or create_rym_search_release_url(album.title))
        .with_thumbnail(album.cover_url)
        .with_author(f"{user.name} rated...", str(user.avatar))
        .with_color(discord.Color(int(RYM_RATING_COLORS[rating.score].lstrip("#"), 16)))
        .build()
    )


def artist_ratings_embed(
    ratings: list[Rating],
    artist: str,
    user_name: str,
    average_score: float,
    start: int = 1,
) -> discord.Embed:
    lines = []

    for i, rating in enumerate(ratings, start=start):
        lines.append(
            f"{i}. {format_release(rating.album)} ({rating.album.release_year}) \\- {format_star_score(rating.score)}",
        )

    title = f"Top {artist} albums for {user_name}"

    description = f"Average score: {format_star_score(average_score)}\n\n"
    description += "\n".join(lines)

    return (
        EmbedBuilder()
        .with_title(title)
        .with_description(description)
        .with_thumbnail(ratings[0].album.cover_url)
        .build()
    )


def ratinks_rank_embed(
    server_name: str,
    ratings: list[Rating],
    start: int = 1,
) -> discord.Embed:
    lines = []

    for i, row in enumerate(ratings, start=start):
        lines.append(f"{i}. <@{row.user}> ({row.rating_count})")

    title = f"{server_name} Ratings Rank"
    description = "\n".join(lines)

    return EmbedBuilder().with_title(title).with_description(description).build()


def ratings_rank_view(server_name: str, ratings: list[Rating]) -> PaginatorView:
    pages = []
    num_pages = ceil(len(ratings) / 10)

    for i in range(num_pages):
        page_ratings = ratings[i * 10 : (i + 1) * 10]
        page = ratinks_rank_embed(server_name, page_ratings, start=i)
        page.set_footer(text=f"Page {i + 1}/{num_pages}")

        pages.append(page)

    return PaginatorView(pages)


def most_rated_releases_embed(albums: list, start: int = 1) -> discord.Embed:
    """Create an embed for the most rated releases."""
    description = "\n".join(
        f"{i}. {format_artist(row.artist)} \\- [{row.title}]({create_rym_search_release_url(row.title)}) (**{row.rating_count}** ratings)"
        for i, row in enumerate(albums, start=start)
    )

    return (
        EmbedBuilder()
        .with_title("Releases with most ratings")
        .with_description(description)
        .build()
    )


def best_rated_artists_embed(
    best_rated_artists: list,
    server_name: str | None = None,
    user_name: str | None = None,
    start: int = 1,
) -> discord.Embed:
    """Create an embed for the best rated artists."""
    title = (
        f"Best rated artists for user {user_name}"
        if user_name
        else f"Best rated artists in {server_name}"
    )
    description = "\n".join(
        f"{i}. {format_artist(row.artist)} ({format_star_score(row.average_score)} from **{row.releases_count}** releases)"
        for i, row in enumerate(best_rated_artists, start=start)
    )

    return EmbedBuilder().with_title(title).with_description(description).build()


def most_rated_artists_embed(
    most_rated_artists: list,
    user_name: str | None,
    server_name: str | None,
    start: int = 1,
) -> discord.Embed:
    """Create an embed for the most rated artists."""
    title = (
        f"Artists with most ratings for user {user_name}"
        if user_name
        else f"Artists with most ratings in {server_name}"
    )
    description = "\n".join(
        f"{i}. {format_artist(row.artist)} (**{row.rating_count}** ratings)"
        for i, row in enumerate(most_rated_artists, start=start)
    )

    return EmbedBuilder().with_title(title).with_description(description).build()


def lyrics_embed(
    lyrics: list[str],
    title: str,
    artist: str,
    _start: int = 1,
) -> discord.Embed:
    """Create an embed for the lyrics."""
    title = f"Lyrics for {artist} - {title}"
    description = "\n".join(lyrics)

    return EmbedBuilder().with_title(title).with_description(description).build()


def comparison_embed(ratings: list, start: int = 1) -> discord.Embed:
    """Create an embed comparing two users' ratings."""
    description = f'<@{ratings[0]["user1"]}> vs <@{ratings[0]["user2"]}>\n\n'

    for row in ratings[start : start + 10]:
        user1_score = row["score1"] / 2
        user2_score = row["score2"] / 2
        description += (
            f"**{row["artist"]}** - *{row["title"]}*\n"
            f"{user1_score:.1f} ⭐ | {user2_score:.1f} ⭐ ({user1_score - user2_score:.1f} ⭐)\n\n"
        )

    return (
        EmbedBuilder()
        .with_title("Rating Comparison")
        .with_description(description)
        .build()
    )


def ratings_per_year_embed(
    ratings: list[Rating],
    user: str,
    start: int = 1,
) -> discord.Embed:
    """Create an embed for the yearly ratings."""
    description = "\n".join(
        f"{i}. {rating.album.release_year} - **{rating.rating_count}** ratings"
        for i, rating in enumerate(ratings, start=start)
    )

    return (
        EmbedBuilder()
        .with_title(f"{user}'s ratings per year")
        .with_description(description)
        .build()
    )


def profile_embed(
    user_name: str,
    average_rating: float,
    number_ratings: int,
) -> discord.Embed:
    """Create an embed for the user profile."""
    description = f"Average rating: {format_star_score(average_rating)}\n"
    description += f"Number of ratings: {number_ratings}\n"

    return EmbedBuilder().with_title(user_name).with_description(description).build()


def samples_embed(
    artist_name: str,
    track_name: str,
    cover_url: str,
    url: str,
    relationships: list[list[dict]],
) -> discord.Embed:
    """Create an embed for the track samples."""
    description = ""

    for songs, subtitle in zip(
        relationships, ["Samples", "Interpolations", "Sampled in"]
    ):
        if len(songs) > 0:
            description = f"### {subtitle}\n"

        for song in songs:
            description += (
                f"- [{song["artist_names"]} - {song["title"]}]({song["url"]})\n"
            )

    description += "\n*Data retrieved from [Genius](https://genius.com/)*"

    return (
        EmbedBuilder()
        .with_title(f"{artist_name} - {track_name}")
        .with_description(description)
        .with_thumbnail(cover_url)
        .with_url(url)
        .build()
    )


def paginate_embeds(
    items: list,
    embed_fn: Callable,
    per_page: int = 10,
    *args,
    **kwargs,
) -> tuple[PaginatorView, list]:
    pages = []
    num_pages = (len(items) + per_page - 1) // per_page

    for i in range(num_pages):
        page_items = items[i * per_page : (i + 1) * per_page]
        embed = embed_fn(page_items, *args, **kwargs, start=i * per_page)
        embed.set_footer(text=f"Page {i + 1}/{num_pages}")
        pages.append(embed)

    view = PaginatorView(pages)

    return view, pages


def format_release(album: Album) -> str:
    url = album.url if album.url else create_rym_search_release_url(album.title)

    return f"[{album.title}]({url})"


def format_artist(artist: str) -> str:
    return f"[{artist}]({create_rym_search_artist_url(artist)})"
