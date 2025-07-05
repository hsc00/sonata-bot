import csv
import html
import re

import requests

from discord.ext import commands
from peewee import fn, IntegrityError

from core.errors import InvalidUserMention, NoRatingsFound, RatingsImportFailed, NoFileAttached
from core.utils import store_album
from database import UserInfo, Rating, Album
from core.embeds import ratings_rank_view, comparison_embed, profile_embed

from core.decorators import disabled


class UsersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @disabled()
    @commands.command()
    async def set_rym(self, ctx: commands.Context, username: str):
        """
        Set your RYM username.
        """

        if not username:
            await ctx.send("Please provide a [RateYourMusic](https://rateyourmusic.com/) username.")

            return

        UserInfo.create(user_id=ctx.author.id, rym_username=username)

        await ctx.send(f"Your RateYourMusic username has been set to **{username}**.")

    @commands.command(alias="setlastfm")
    async def set_lastfm(self, ctx: commands.Context, *, username: str | None):
        """
        Set your last.fm username.
        """

        if not username:
            await ctx.send("Please provide a [last.fm](https://www.last.fm/) username.")

            return

        user_info, created = UserInfo.get_or_create(
            user_id=str(ctx.author.id),
            defaults={'lastfm_username': username}
        )

        if not created:
            user_info.lastfm_username = username
            user_info.save()

        await ctx.send(f"Your last.fm username has been set to **{username}**.")

    @commands.command(aliases=["rr"])
    async def ratings_rank(self, ctx: commands.Context):
        """
        Get a ranking of users by their number of ratings.
        """

        ratings = (
            Rating
            .select(Rating.user, fn.COUNT(Rating.id).alias('rating_count'))
            .group_by(Rating.user)
            .order_by(fn.COUNT(Rating.id).desc())
            .limit(100)
        )

        if not ratings:
            raise NoRatingsFound()

        view = ratings_rank_view(ctx.guild.name, ratings)

        await ctx.send(embed=view.pages[0], view=view)

    @disabled()
    @commands.command(aliases=["c"])
    async def compare(self, ctx: commands.Context, *, query: str | None = None):
        """
        Compare your ratings with another user.
        """

        if not query:
            raise InvalidUserMention()

        match = re.match(r"<@!?(\d+)>", query)

        if not match:
            raise InvalidUserMention(query)

        user_id = str(ctx.author.id)
        other_user_id = match.group(1)

        # Fetch ratings for albums in common between the two users
        r1 = Rating.alias()
        r2 = Rating.alias()

        common_ratings = (
            r1.select(
                r1.album,
                r1.user.alias("user1"),
                r1.score.alias("score1"),
                r2.user.alias("user2"),
                r2.score.alias("score2"),
                Album.title,
                Album.artist
            )
            .join(Album, on=(r1.album == Album.id))
            .switch(r1)
            .join(r2, on=(r1.album == r2.album))
            .where(
                (r1.user == user_id) &
                (r2.user == other_user_id)
            )
            .order_by(r1.score - r2.score)
            .limit(100)
        )

        if common_ratings.limit(1).first() is None:
            await ctx.send("❌ No ratings in common found.")

            return

        # Compare ratings and create an embed
        embed = comparison_embed(list(common_ratings.dicts()))

        await ctx.send(embed=embed)

    @commands.command()
    async def profile(self, ctx: commands.Context, *, query: str | None = None):
        user_id = ctx.author.id if query is None else query
        user_name = ctx.author.display_name if query is None else (
            await ctx.guild.fetch_member(int(user_id))).display_name
        average_rating = (
            Rating
            .select(fn.AVG(Rating.score).alias('average_rating'))
            .where(Rating.user == user_id)
            .scalar()
        )

        embed = profile_embed(user_name, average_rating)

        await ctx.send(embed=embed)

    @commands.command(name="import", aliases=["i"])
    async def import_ratings(self, ctx):
        """
        Import ratings from RYM.
        """

        if not ctx.message.attachments:
            raise NoFileAttached()

        attachment_url = ctx.message.attachments[0].url
        response = requests.get(attachment_url)

        if response.status_code != 200:
            raise RatingsImportFailed()

        try:
            # Clean existing ratings for the user
            Rating.delete().where(Rating.user == ctx.author.id).execute()

            # Read the CSV file
            rows = list(csv.DictReader(response.text.splitlines()))

            with ctx.typing():
                for row in rows:
                    await self.import_rating(ctx.author.id, row)

                await ctx.send(content=f"✅ Imported ratings successfully for user <@{ctx.message.author.id}>.")

        except Exception:
            raise RatingsImportFailed()

    @staticmethod
    async def import_rating(user_id: int, row):
        """
        Import a single rating.
        """

        score = int(row["Rating"])

        # Skip wishlisted albums
        if score == 0:
            return

        if score < 1 or score > 10:
            raise ValueError("Score must be between 1 and 10")

        title = html.unescape(row["Title"])

        # Search for the album in the database
        try:
            album = Album.get(Album.title == title)

        # If the album is not found, create it
        except Album.DoesNotExist:
            first_name = row[' First Name'] or None
            last_name = row['Last Name']

            artist = html.unescape(f"{first_name + " " if first_name else ""}{last_name}")

            release_year = int(row.get("Release_Date") or "0")

            album = Album(
                title=title,
                artist=artist,
                release_year=release_year,
            )

            album.save(force_insert=True)
            store_album(album)

        try:
            Rating.create(
                user=user_id,
                score=score,
                album=album,
            )

        except IntegrityError:
            pass


async def setup(bot):
    await bot.add_cog(UsersCog(bot))
