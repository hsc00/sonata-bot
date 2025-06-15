import csv
import html
import requests

from typing import Optional

from discord.ext import commands
from peewee import fn, IntegrityError

from database import UserInfo, Rating, Album
from utils.embeds import make_ratings_rank_view

from utils import utils


class UsersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command()
    async def set_lastfm(self, ctx: commands.Context, *, username: Optional[str]):
        """
        Set your last.fm username.
        """

        if not username:
            await ctx.send("Please provide a [last.fm](https://www.last.fm/) username.")

            return

        UserInfo.create(user_id=str(ctx.author.id), lastfm_username=username)

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
            await ctx.send("No ratings found.")

            return

        view = make_ratings_rank_view(ctx.guild.name, ratings)

        await ctx.send(embed=view.pages[0], view=view)

    @commands.command(name="import", aliases=["i"])
    async def import_ratings(self, ctx):
        """
        Import ratings from RYM.
        """

        if not ctx.message.attachments:
            await ctx.send("❌ No file attached.")

            return

        message = await ctx.send(f"📥 Importing ratings for user <@{ctx.message.author.id}>...")

        attachment_url = ctx.message.attachments[0].url
        response = requests.get(attachment_url)

        if response.status_code != 200:
            await message.edit(content="❌ Failed to import ratings.")

            return

        try:
            # Clean existing ratings for the user
            Rating.delete().where(Rating.user == ctx.author.id).execute()

            # Read the CSV file
            rows = list(csv.DictReader(response.text.splitlines()))

            for row in rows:
                await self.import_rating(ctx.author.id, row)

            await message.edit(content=f"✅ Imported ratings successfully for user <@{ctx.message.author.id}>.")

        except Exception:
            await message.edit(content=f"❌ Failed to import ratings.")

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
            utils.store_album(album)

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
