from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Literal

from api.sputnik import fetch_new_releases
from core.decorators import disabled
from core.embeds import (
    album_embed,
    album_of_the_year_embed,
    best_rated_albums_embed,
    most_rated_releases_embed,
    paginate_embeds,
    rating_embed,
    ratings_per_year_embed,
    who_rated_album_embed,
)
from core.errors import InvalidYearError, NoRatingsFoundError
from core.utils import fetch_album
from database.models import Album, Rating
from discord import Message, User, app_commands
from discord.ext import commands
from peewee import fn

logger = logging.getLogger(__name__)


class ReleasesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        # Prevent bot from responding to itself
        if message.author == self.bot.user:
            return

        url_pattern = re.compile(
            r"https?://(?:www\.)?rateyourmusic\.com/release/.+?/(.+)?/\S*",
        )

        if matches := url_pattern.search(message.content):
            album, artist = (
                x.replace("-", " ") for x in matches.groups()[0].split("/")
            )

            ctx = await self.bot.get_context(message)

            await self.release.callback(self, ctx, release_name=f"{artist} {album}")

    @commands.hybrid_command(
        name="release", aliases=["r", "a", "album"], with_app_command=True
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        release_name="Name of release (defaults to last played album)",
    )
    async def release(
        self,
        ctx: commands.Context,
        *,
        release_name: str | None = None,
    ) -> None:
        """Get information about a given release."""
        release = await fetch_album(str(ctx.author.id), release_name)

        if release is None:
            logger.error("No album found for %s", release_name)

            return

        embed = album_embed(release)

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="whoratedrelease",
        aliases=["wr", "wa", "who_rated_album"],
    )
    @app_commands.describe(
        release_name="Name of release (defaults to last played album)",
    )
    async def who_rated_release(
        self,
        ctx: commands.Context,
        *,
        release_name: str | None = None,
    ) -> None:
        """Get the users who rated a given release."""
        release = await fetch_album(str(ctx.author.id), release_name)

        if release is None:
            logger.error("No album found for %s", release_name)

            return

        ratings = list(
            Rating.select()
            .where(Rating.album == release)
            .order_by(Rating.score.desc())
            .iterator(),
        )

        if len(ratings) == 0:
            raise NoRatingsFoundError(release.title)

        view, pages = paginate_embeds(
            ratings,
            who_rated_album_embed,
            per_page=10,
            album=release,
            user_id=ctx.message.author.id,
            server_name=getattr(ctx.guild, "name", ""),
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="bestratedreleases",
        aliases=["brr", "brab", "best_rated_albums"],
    )
    async def best_rated_releases(self, ctx: commands.Context) -> None:
        """Get the best rated releases in the server."""
        # Select releases with more than 3 ratings
        albums: list[Album] = (
            Album.select().join(Rating).group_by(Album).having(fn.COUNT(Rating.id) > 3)
        )

        if len(albums) == 0:
            await ctx.send("No albums found with more than 3 ratings.")

            return

        # Compute average rating and weighted rating for each release
        w1, w2 = 7, 0.4

        albums_with_weighted_rating = []

        for album in albums:
            rating_sum = (
                Rating.select(fn.SUM(Rating.score))
                .where(Rating.album == album)
                .scalar()
            )

            total_ratings = (
                Rating.select(fn.COUNT(Rating.id)).where(Rating.album == album).scalar()
            )

            average_rating = rating_sum / total_ratings
            weighted_rating = (average_rating * w1) + (total_ratings * w2)

            albums_with_weighted_rating.append((album, average_rating, weighted_rating))

        # Sort releases by their weighted rating in descending order
        sorted_releases = sorted(
            albums_with_weighted_rating,
            key=lambda x: x[2],
            reverse=True,
        )

        top_releases = sorted_releases[:100]

        # TODO: Include number of ratings

        view, pages = paginate_embeds(
            top_releases,
            best_rated_albums_embed,
            per_page=10,
            server_name=getattr(ctx.guild, "name", ""),
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="mostratedreleases",
        aliases=["mrr", "mrab", "most_rated_albums"],
    )
    async def most_rated_releases(
        self,
        ctx: commands.Context,
    ) -> None:
        """Get the most rated releases in the server."""
        # Select releases with more than 3 ratings
        most_rated_releases = (
            Album.select(
                Album.artist,
                Album.title,
                fn.COUNT(Rating.id).alias("rating_count"),
            )
            .join(Rating)
            .group_by(Album)
            .order_by(fn.COUNT(Rating.id).desc())
            .limit(100)
        )

        if len(most_rated_releases) == 0:
            await ctx.send("No albums found with more than 3 ratings.")

            return

        view, pages = paginate_embeds(
            most_rated_releases,
            most_rated_releases_embed,
            per_page=10,
        )

        await ctx.send(embed=pages[0], view=view)

    @app_commands.describe(filter="Filter ratings by roast (<= 2.0) or glaze (>= 3.0)")
    @commands.hybrid_command(name="randomrating", aliases=["rdr"])
    async def random_rating(
        self,
        ctx: commands.Context,
        filter: Literal["roast", "glaze"] | None = None,
    ) -> None:
        """Get a random rating."""
        if filter == "roast":
            rating = (
                Rating.select()
                .where(
                    Rating.score <= 2.0,
                )
                .order_by(fn.Random())
                .first()
            )

        elif filter == "glaze":
            rating = (
                Rating.select()
                .where(
                    Rating.score >= 3.0,
                )
                .order_by(fn.Random())
                .first()
            )

        else:
            rating = Rating.select().order_by(fn.Random()).first()

        if rating is None:
            await ctx.send("No ratings found.")

            return

        user = await ctx.bot.fetch_user(rating.user)

        await ctx.send(embed=rating_embed(user, rating))

    @commands.hybrid_command(name="aoty", with_app_command=True)
    @app_commands.describe(
        year="Year to get the best rated albums from (defaults to current year)",
        user="User to get the ratings from (defaults to the command author)",
    )
    async def album_of_the_year(
        self,
        ctx: commands.Context,
        year: int | None,
        user: User | None = None,
    ) -> None:
        """Get the best rated albums of a given year."""

        if year is None:
            year = datetime.now(tz=timezone.utc).year

        elif year < 1900 or year > datetime.now(tz=timezone.utc).year:
            raise InvalidYearError(year)

        if not user:
            user = ctx.author

        user_id = str(user.id)
        user_name = user.display_name

        # Select ratings from the given year
        ratings = (
            Rating.select()
            .join(Album)
            .where((Album.release_year == year) & (Rating.user == user_id))
            .order_by(Rating.score.desc())
        )

        if len(ratings) == 0:
            await ctx.send(f"❌ No ratings found for the year {year}.")

            return

        view, pages = paginate_embeds(
            ratings,
            album_of_the_year_embed,
            per_page=10,
            user_name=user_name,
            year=year,
        )

        await ctx.send(embed=pages[0], view=view)

    @disabled()
    @commands.command(aliases=["rpy"])
    async def ratings_per_year(
        self,
        ctx: commands.Context,
        *,
        query: str | None = None,
    ) -> None:
        """Get the total number of ratings per year."""
        if query is None:
            user_id = str(ctx.author.id)

        else:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                await ctx.send("Please provide a valid user mention.")

                return

            user_id = match.group(1)

        # Select ratings grouped by year of the release
        ratings = (
            Rating.select(Album, fn.COUNT(Rating.id).alias("rating_count"))
            .join(Album)
            .where(Rating.user == user_id)
            .group_by(Album.release_year)
            .order_by(Album.release_year.desc())
        )

        if len(ratings) == 0:
            await ctx.send("No ratings found for this user.")

            return

        embed = ratings_per_year_embed(ratings, user_id)

        await ctx.send(embed=embed)

    @commands.command(aliases=["nr"])
    async def new_releases(
        self,
        ctx: commands.Context,
        *,
        query: str | None = None,
    ) -> None:
        """Get the new releases of the week."""
        channel_id = 725329619515080769
        channel = self.bot.get_channel(channel_id)
        new_releases = fetch_new_releases()

        if not new_releases:
            await channel.send("💔 No new releases found.")

            return

        ctx.channel = channel

        for release in new_releases:
            await self.release.callback(self, ctx, release_name=release)
