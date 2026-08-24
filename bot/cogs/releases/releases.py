from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Literal

from api.sputnik import fetch_new_releases
from core.constants import (
    RANDOM_RATING_GLAZE_THRESHOLD,
    RANDOM_RATING_ROAST_THRESHOLD,
    RATINGS_MIN_THRESHOLD,
    RELEASE_RATING_W1,
    RELEASE_RATING_W2,
)
from core.decorators import disabled
from core.embeds import (
    album_embed,
    album_of_the_year_embed,
    best_rated_releases_embed,
    lowest_rated_albums_of_the_year_embed,
    most_rated_releases_embed,
    paginate_embeds,
    rating_embed,
    ratings_per_year_embed,
    who_rated_release_embed,
    worst_rated_releases_embed,
)
from core.errors import (
    InvalidUserMentionError,
    InvalidYearError,
    NoRatingsFoundError,
    SonataError,
)
from core.utils import fetch_album
from database.models import Album, Rating
from discord import Member, Message, User, app_commands
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
        aliases=["wr", "wa", "who_rated_album", "who_rated_release"],
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
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        release = await fetch_album(str(ctx.author.id), release_name)

        if release is None:
            logger.error("No album found for %s", release_name)

            return

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        ratings = list(
            Rating.select()
            .where((Rating.album == release) & (Rating.user.in_(guild_member_ids)))
            .order_by(Rating.score.desc())
            .iterator(),
        )

        if len(ratings) == 0:
            raise NoRatingsFoundError(str(release.title))

        average_score = (sum(rating.score for rating in ratings) / len(ratings)) / 2

        view, pages = paginate_embeds(
            ratings,
            who_rated_release_embed,
            per_page=10,
            album=release,
            average_score=average_score,
            num_ratings=len(ratings),
            user_id=ctx.message.author.id,
            server_name=getattr(ctx.guild, "name", ""),
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="bestratedreleases",
        aliases=["brr", "brab", "best_rated_albums"],
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def best_rated_releases(self, ctx: commands.Context) -> None:
        """Get the best rated releases in the server."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        async with ctx.typing():
            # Select releases with more than 3 ratings
            albums = (
                Album.select(
                    Album,
                    fn.SUM(Rating.score).alias("rating_sum"),
                    fn.COUNT(Rating.id).alias("rating_count"),
                )
                .join(Rating)
                .where(Rating.user.in_(guild_member_ids))
                .group_by(Album.id)
                .having(fn.COUNT(Rating.id) > RATINGS_MIN_THRESHOLD)
            )

            if len(albums) == 0:
                await ctx.send(
                    f"No albums found with more than {RATINGS_MIN_THRESHOLD} ratings.",
                )

                return

            # Compute average rating and weighted rating for each release
            w1, w2 = RELEASE_RATING_W1, RELEASE_RATING_W2

            albums_with_weighted_rating = []

            for album in albums:
                average_rating = album.rating_sum / album.rating_count
                weighted_rating = (average_rating * w1) + (album.rating_count * w2)

                albums_with_weighted_rating.append(
                    (album, average_rating, weighted_rating, album.rating_count),
                )

            # Sort releases by their weighted rating in descending order
            sorted_releases = sorted(
                albums_with_weighted_rating,
                key=lambda x: x[2],
                reverse=True,
            )

            top_releases = sorted_releases[:100]

            view, pages = paginate_embeds(
                top_releases,
                best_rated_releases_embed,
                per_page=10,
                server_name=getattr(ctx.guild, "name", ""),
            )

            await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="worstratedreleases",
        aliases=["wrr", "wrab", "worst_rated_albums"],
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def worst_rated_releases(self, ctx: commands.Context) -> None:
        """Get the worst rated releases in the server."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        async with ctx.typing():
            albums = (
                Album.select(
                    Album,
                    fn.SUM(Rating.score).alias("rating_sum"),
                    fn.COUNT(Rating.id).alias("rating_count"),
                )
                .join(Rating)
                .where(Rating.user.in_(guild_member_ids))
                .group_by(Album.id)
                .having(fn.COUNT(Rating.id) > 3)
            )

            if len(albums) == 0:
                await ctx.send("No albums found with more than 3 ratings.")

                return

            w1, w2 = RELEASE_RATING_W1, RELEASE_RATING_W2

            albums_with_weighted_rating = []

            for album in albums:
                average_rating = album.rating_sum / album.rating_count
                weighted_rating = (average_rating * w1) + (album.rating_count * w2)

                albums_with_weighted_rating.append(
                    (album, average_rating, weighted_rating, album.rating_count),
                )

            sorted_releases = sorted(
                albums_with_weighted_rating,
                key=lambda x: x[2],
                reverse=False,
            )

            worst_releases = sorted_releases[:100]

            view, pages = paginate_embeds(
                worst_releases,
                worst_rated_releases_embed,
                per_page=10,
                server_name=getattr(ctx.guild, "name", ""),
            )

            await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="mostratedreleases",
        aliases=["mrr", "mrab", "most_rated_albums"],
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def most_rated_releases(
        self,
        ctx: commands.Context,
    ) -> None:
        """Get the most rated releases in the server."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        most_rated_releases = (
            Album.select(
                Album.artist,
                Album.title,
                fn.COUNT(Rating.id).alias("rating_count"),
            )
            .where(Rating.user.in_(guild_member_ids))
            .join(Rating)
            .group_by(Album)
            .order_by(fn.COUNT(Rating.id).desc())
            .limit(100)
        )

        if len(most_rated_releases) == 0:
            raise NoRatingsFoundError

        view, pages = paginate_embeds(
            most_rated_releases,
            most_rated_releases_embed,
            per_page=10,
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(name="randomrating", aliases=["rdr"])
    @app_commands.describe(
        filter_type="Filter ratings by roast (<= 2.0) or glaze (>= 4.5)",
    )
    async def random_rating(
        self,
        ctx: commands.Context,
        filter_type: Literal["roast", "glaze"] | None = None,
    ) -> None:
        """Get a random rating."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        if ctx.message and filter_type is None:
            parts = ctx.message.content.split(maxsplit=1)

            if len(parts) > 1:
                filter_type = parts[1].strip().lower()

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        if filter_type == "roast":
            rating = (
                Rating.select()
                .where(
                    (Rating.score <= RANDOM_RATING_ROAST_THRESHOLD)
                    & (Rating.user.in_(guild_member_ids)),
                )
                .order_by(fn.Random())
                .first()
            )

        elif filter_type == "glaze":
            rating = (
                Rating.select()
                .where(
                    (Rating.score >= RANDOM_RATING_GLAZE_THRESHOLD)
                    & (Rating.user.in_(guild_member_ids)),
                )
                .order_by(fn.Random())
                .first()
            )

        else:
            rating = (
                Rating.select()
                .where(Rating.user.in_(guild_member_ids))
                .order_by(fn.Random())
                .first()
            )

        if rating is None:
            raise NoRatingsFoundError

        user = await ctx.bot.fetch_user(rating.user)

        await ctx.send(embed=rating_embed(user, rating))

    @commands.hybrid_command(name="aoty", with_app_command=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        year="Year to get the best rated albums from (defaults to current year)",
        user="User to get the ratings from (defaults to the command author)",
    )
    async def album_of_the_year(
        self,
        ctx: commands.Context,
        year: int | None,
        user: User | Member | None = None,
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

    @commands.hybrid_command(name="laoty", with_app_command=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        year="Year to get the worst rated albums from (defaults to current year)",
        user="User to get the ratings from (defaults to the command author)",
    )
    async def lowest_rated_albums_of_the_year(
        self,
        ctx: commands.Context,
        year: int | None,
        user: User | Member | None = None,
    ) -> None:
        """Get the lowest rated albums of a given year."""

        if year is None:
            year = datetime.now(tz=timezone.utc).year

        elif year < 1900 or year > datetime.now(tz=timezone.utc).year:
            raise InvalidYearError(year)

        if not user:
            user = ctx.author

        user_id = str(user.id)
        user_name = user.display_name

        # Select ratings from the given year, sorted by lowest score first
        ratings = (
            Rating.select()
            .join(Album)
            .where((Album.release_year == year) & (Rating.user == user_id))
            .order_by(Rating.score.asc())
        )

        if len(ratings) == 0:
            await ctx.send(f"❌ No ratings found for the year {year}.")

            return

        view, pages = paginate_embeds(
            ratings,
            lowest_rated_albums_of_the_year_embed,
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
                raise InvalidUserMentionError(query)

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
            raise NoRatingsFoundError

        embed = ratings_per_year_embed(ratings, user_id)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="newreleases", aliases=["nr"], with_app_command=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def new_releases(self, ctx: commands.Context) -> None:
        """Get the new releases of the week."""
        new_releases = fetch_new_releases()

        if not new_releases:
            raise SonataError("💔 No new releases found.")

        for release_name in new_releases:
            release = await fetch_album(str(ctx.author.id), release_name)

            if (
                release is None
                or release.release_year != datetime.now(tz=timezone.utc).year
            ):
                continue

            embed = album_embed(release)

            await ctx.send(embed=embed)
