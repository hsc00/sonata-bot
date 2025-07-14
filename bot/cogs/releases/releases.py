import logging
import math
import re
from collections import defaultdict
from datetime import datetime
from typing import Literal

from discord.ext import commands
from discord import Message

from peewee import fn

from api.sputnik import fetch_new_releases
from core.errors import NoRatingsFound, InvalidYear, InvalidUserMention
from core.utils import fetch_album, SonataError
from core.decorators import disabled
from core.embeds import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.models import Album, Rating

logger = logging.getLogger(__name__)


class ReleasesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            self.new_releases,
            CronTrigger(day_of_week='fri', hour=0, minute=0),  # Every Friday at 00:00
            name="New Releases",
        )

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # Prevent bot from responding to itself
        if message.author == self.bot.user:
            return

        url_pattern = re.compile(r"https?://(?:www\.)?rateyourmusic\.com/release/.+?/(.+)?/\S*")

        if matches := url_pattern.search(message.content):
            album, artist = map(lambda x: x.replace("-", " "), matches.groups()[0].split("/"))

            ctx = await self.bot.get_context(message)

            await self.release.callback(self, ctx, release_name=f"{artist} {album}")

    @commands.hybrid_command(name="release", aliases=["r", "a", "album"])
    async def release(
            self,
            ctx: commands.Context,
            *,
            release_name: str | None = None
    ) -> None:
        """
        Get information about a given release.
        """

        release = await fetch_album(str(ctx.author.id), release_name)

        if release is None:
            logger.error("No album found for %s", release_name)

            return

        embed = album_embed(release)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="whoratedrelease", aliases=["wr", "wa", "who_rated_album"])
    async def who_rated_release(
            self,
            ctx: commands.Context,
            *,
            release_name: str | None = None
    ) -> None:
        """
        Get the users who rated a given release.
        """

        release = await fetch_album(str(ctx.author.id), release_name)

        if release is None:
            logger.error("No album found for %s", release_name)

            return

        ratings = list(
            Rating.select()
            .where(Rating.album == release)
            .order_by(Rating.score.desc())
            .iterator()
        )

        if len(ratings) == 0:
            raise NoRatingsFound(release.title)

        view, pages = paginate_embeds(
            ratings,
            who_rated_album_embed,
            per_page=10,
            album=release,
            user_id=ctx.message.author.id,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(name="bestratedreleases", aliases=["brr", "brab", "best_rated_albums"])
    async def best_rated_releases(self, ctx: commands.Context) -> None:
        """
        Get the best rated releases in the server.
        """

        # Select releases with more than 3 ratings
        albums: list[Album] = (
            Album
            .select()
            .join(Rating)
            .group_by(Album)
            .having(fn.COUNT(Rating.id) > 3)
        )

        if len(albums) == 0:
            await ctx.send("No albums found with more than 3 ratings.")

            return

        # Compute average rating and weighted rating for each release
        w1, w2 = 7, 0.4

        albums_with_weighted_rating = []

        for album in albums:
            rating_sum = Rating.select(fn.SUM(Rating.score)) \
                .where(Rating.album == album) \
                .scalar()

            total_ratings = Rating.select(fn.COUNT(Rating.id)) \
                .where(Rating.album == album) \
                .scalar()

            average_rating = rating_sum / total_ratings
            weighted_rating = (
                    (average_rating * w1) +
                    (total_ratings * w2)
            )

            albums_with_weighted_rating.append((album, average_rating, weighted_rating))

        # Sort releases by their weighted rating in descending order
        sorted_releases = sorted(
            albums_with_weighted_rating,
            key=lambda x: x[2],
            reverse=True
        )

        top_releases = sorted_releases[:100]

        # TODO: Include number of ratings

        view, pages = paginate_embeds(
            top_releases,
            best_rated_albums_embed,
            per_page=10,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(name="mostratedreleases", aliases=["mrr", "mrab", "most_rated_albums"])
    async def most_rated_releases(
            self,
            ctx: commands.Context,
    ) -> None:
        """
        Get the most rated releases in the server.
        """

        # Select releases with more than 3 ratings
        most_rated_releases = (
            Album
            .select(Album.artist, Album.title, fn.COUNT(Rating.id).alias('rating_count'))
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

    @commands.hybrid_command(name="randomrating", aliases=["rdr"])
    async def random_rating(
            self,
            ctx: commands.Context,
            filter: Literal["roast", "glaze"] | None = None
    ) -> None:
        """
        Get a random rating.
        """

        if filter == "roast":
            rating = Rating.select().where(
                Rating.score <= 2.0,
            ).order_by(fn.Random()).first()

        elif filter == "glaze":
            rating = Rating.select().where(
                Rating.score >= 3.0,
            ).order_by(fn.Random()).first()

        else:
            rating = Rating.select().order_by(fn.Random()).first()

        if rating is None:
            await ctx.send("No ratings found.")

            return

        user = await ctx.bot.fetch_user(rating.user)

        await ctx.send(embed=rating_embed(user, rating))

    @commands.hybrid_command(name="aoty")
    async def album_of_the_year(
            self,
            ctx: commands.Context,
            year: int | None,
            user: discord.User | None = None
    ) -> None:
        """
        Get the best rated albums of a given year.
        """

        if year is None:
            year = datetime.now().year

        else:
            if year < 1900 or year > datetime.now().year:
                raise InvalidYear(year)

        if not user:
            user = ctx.author

        user_id = str(user.id)
        user_name = user.display_name

        # Select ratings from the given year
        ratings = (
            Rating
            .select()
            .join(Album)
            .where(
                (Album.release_year == year) &
                (Rating.user == user_id)
            )
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
    @commands.command(aliases=["tg"])
    async def top_genres(self, ctx: commands.Context, *, query: str | None = None) -> None:
        """
        Get the top genres of a user.
        """

        if query is None:
            user_id = str(ctx.author.id)

        else:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                raise InvalidUserMention(query)

            user_id = match.group(1)

        genre_scores = defaultdict(list)

        # Fetch albums and their ratings
        for album in Album.select().prefetch(Rating):
            if not album.genres:
                continue

            genres = [g.strip() for g in album.genres.split(',')]
            scores = [r.score for r in album.ratings]

            if not scores:
                continue

            for genre in genres:
                genre_scores[genre].extend(scores)

        # Aggregate
        genre_stats = []

        for genre, scores in genre_scores.items():
            avg = sum(scores) / len(scores)
            count = len(scores)
            weighted = avg * math.log(1 + count)
            genre_stats.append((genre, avg, count, weighted))

        # Sort by weighted score
        genre_stats.sort(key=lambda x: x[3], reverse=True)

        embed = top_genres_embed(genre_stats[:20])

        await ctx.send(embed=embed)

    @disabled()
    @commands.command(aliases=["rpy"])
    async def ratings_per_year(self, ctx: commands.Context, *, query: str | None = None) -> None:
        """
        Get the total number of ratings per year.
        """

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
            Rating
            .select(
                Album,
                fn.COUNT(Rating.id).alias('rating_count')
            )
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

    async def new_releases(self):
        """
        Get the new releases of the week.
        """

        channel_id = 1245325666900115517
        channel = self.bot.get_channel(channel_id)
        new_releases = fetch_new_releases()

        if not new_releases:
            await channel.send("❌ No new releases found.")

            return

        for release in new_releases:
            try:
                await self.release.callback(self, channel, query=release)

            except SonataError:
                continue
