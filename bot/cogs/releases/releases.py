import logging
import re
from datetime import datetime
from typing import Optional

from discord.ext import commands

from database import Album, Rating
from peewee import fn

from utils import fetch_album
from utils.embeds import make_album_embed, make_who_rated_album_embed, make_best_rated_albums_embed, make_rating_embed, \
    make_album_of_the_year_embed, make_most_rated_releases_embed
from utils.views import PaginatorView

logger = logging.getLogger(__name__)


class ReleasesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["r"])
    async def album(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
        """
        Get information about a given album.
        """

        album = await fetch_album(str(ctx.author.id), query)

        if album is None:
            logger.error("No album found for %s", query)

            return

        embed = make_album_embed(album)

        await ctx.send(embed=embed)

    @commands.command(aliases=["wr", "wrr"])
    async def who_rated_release(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
        """
        Get the users who rated a given release.
        """

        album = await fetch_album(str(ctx.author.id), query)

        if album is None:
            return

        ratings = list(
            Rating.select()
            .where(Rating.album == album)
            .order_by(Rating.score.desc())
            .iterator()
        )

        if len(ratings) == 0:
            await ctx.send(f'No ratings exist for "{album.title}".')

            return

        embed = make_who_rated_album_embed(album, ratings, ctx.message.author.id, ctx.guild.name)

        await ctx.send(embed=embed)

    @commands.command(aliases=["brr"])
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

        pages = []
        num_pages = 10

        for i in range(num_pages):
            page_releases = top_releases[i * 10:(i + 1) * 10]
            page = make_best_rated_albums_embed(page_releases, ctx.guild.name)
            page.set_footer(text=f"Page {i + 1}/{num_pages}")

            pages.append(page)

        view = PaginatorView(pages)

        await ctx.send(embed=pages[0], view=view)

    @commands.command(aliases=["mrr"])
    async def most_rated_releases(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
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
            .limit(10)
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

        embed = make_most_rated_releases_embed(most_rated_releases)

        await ctx.send(embed=embed)

    @commands.command(aliases=["rdr"])
    async def random_rating(self, ctx: commands.Context, *, query: Optional[str]) -> None:
        """
        Get a random rating.
        """

        rating = Rating.select().order_by(fn.Random()).first()

        if rating is None:
            await ctx.send("No ratings found.")

            return

        # TODO: Update album details if they are missing

        user = await ctx.bot.fetch_user(rating.user)

        await ctx.send(embed=make_rating_embed(user, rating))

    @commands.command(aliases=["aoty"])
    async def album_of_the_year(self, ctx: commands.Context, *, query: Optional[str]) -> None:
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
                await ctx.send("Please provide a valid year.")

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

        embed = make_album_of_the_year_embed(ratings, ctx.message.author, year)

        await ctx.send(embed=embed)
