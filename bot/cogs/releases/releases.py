import logging
import re
from datetime import datetime

from discord.ext import commands
from discord import Message

from peewee import fn

from utils import fetch_album, paginate_embeds, SonataError, disabled
from utils.embeds import *

from database.models import Album, Rating

logger = logging.getLogger(__name__)


class ReleasesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # Prevent bot from responding to itself
        if message.author == self.bot.user:
            return

        url_pattern = re.compile(r"https?://(?:www\.)?rateyourmusic\.com/release/.+?/(.+)?/\S*")

        if matches := url_pattern.search(message.content):
            album, artist = map(lambda x: x.replace("-", " "), matches.groups()[0].split("/"))

            ctx = await self.bot.get_context(message)

            await self.release.callback(self, ctx, query=f"{artist} {album}")

    @commands.command(aliases=["r", "a", "album"])
    async def release(self, ctx: commands.Context, *, query: str | None = None) -> None:
        """
        Get information about a given release.
        """

        try:
            release = await fetch_album(str(ctx.author.id), query)

        except SonataError as e:
            await ctx.send(str(e))

            return

        if release is None:
            logger.error("No album found for %s", query)

            return

        embed = make_album_embed(release)

        await ctx.send(embed=embed)

    @commands.command(aliases=["wr", "wa", "who_rated_album"])
    async def who_rated_release(self, ctx: commands.Context, *, query: str | None = None) -> None:
        """
        Get the users who rated a given release.
        """

        try:
            release = await fetch_album(str(ctx.author.id), query)

        except SonataError as e:
            await ctx.send(str(e))

            return

        if release is None:
            return

        ratings = list(
            Rating.select()
            .where(Rating.album == release)
            .order_by(Rating.score.desc())
            .iterator()
        )

        if len(ratings) == 0:
            await ctx.send(f'❌ No ratings exist for "{release.title}".')

            return

        view, pages = paginate_embeds(
            ratings,
            make_who_rated_album_embed,
            per_page=10,
            album=release,
            user_id=ctx.message.author.id,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.command(aliases=["brr", "brab", "best_rated_albums"])
    async def best_rated_releases(self, ctx: commands.Context) -> None:
        """
        Get the best rated releases in the server or for a specific user.
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
            make_best_rated_albums_embed,
            per_page=10,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.command(aliases=["mrr", "mrab", "most_rated_albums"])
    async def most_rated_releases(self, ctx: commands.Context, *, query: str | None = None) -> None:
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

        if query:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                await ctx.send("Please provide a valid user mention.")

                return

            user_id = match.group(1)

            most_rated_releases = most_rated_releases.where(Rating.user == user_id)

        if len(most_rated_releases) == 0:
            await ctx.send("No albums found with more than 3 ratings.")

            return

        view, pages = paginate_embeds(
            most_rated_releases,
            make_most_rated_releases_embed,
            per_page=10,
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.command(aliases=["rdr"])
    async def random_rating(self, ctx: commands.Context, *, query: str | None) -> None:
        """
        Get a random rating.
        """

        if query == "roast":
            rating = Rating.select().where(
                Rating.score <= 2.0,
            ).order_by(fn.Random()).first()

        elif query == "glaze":
            rating = Rating.select().where(
                Rating.score >= 3.0,
            ).order_by(fn.Random()).first()

        else:
            rating = Rating.select().order_by(fn.Random()).first()

        if rating is None:
            await ctx.send("No ratings found.")

            return

        # TODO: Update album details if they are missing

        user = await ctx.bot.fetch_user(rating.user)

        await ctx.send(embed=make_rating_embed(user, rating))

    @commands.command(aliases=["aoty"])
    async def album_of_the_year(self, ctx: commands.Context, *, query: str | None) -> None:
        """
        Get the best rated albums of a given year.
        """

        if query is None:
            year = datetime.now().year

        else:
            try:
                year = int(query)

                if year < 1900 or year > datetime.now().year:
                    raise ValueError

            except ValueError:
                await ctx.send("❌ Please provide a valid year.")

                return

        # Select ratings from the given year
        ratings = (
            Rating
            .select()
            .join(Album)
            .where(
                (Album.release_year == year) &
                (Rating.user == str(ctx.author.id))
            )
            .order_by(Rating.score.desc())
        )

        if len(ratings) == 0:
            await ctx.send(f"No ratings found for the year {year}.")

            return

        view, pages = paginate_embeds(
            ratings,
            make_album_of_the_year_embed,
            per_page=10,
            user=ctx.message.author,
            year=year,
        )

        await ctx.send(embed=pages[0], view=view)

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

        embed = ratings_per_year(ratings, user_id)

        await ctx.send(embed=embed)
