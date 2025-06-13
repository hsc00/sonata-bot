import csv
import discord
import html
import requests
import textwrap

from discord.ext import commands
from database import *
from utils.views import PaginatorView

import utils


class RatingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="import", aliases=["i"])
    async def import_ratings(self, ctx):
        """
        Import ratings from RYM.
        """

        if not ctx.message.attachments:
            await ctx.send("No file attached.")

            return

        attachment_url = ctx.message.attachments[0].url
        response = requests.get(attachment_url)

        if response.status_code != 200:
            await ctx.send("Failed to import ratings.")

            return

        # Clean existing ratings for the user
        Rating.delete().where(Rating.user == ctx.author.id).execute()

        # Read the CSV file
        rows = list(csv.DictReader(response.text.splitlines()))

        for row in rows:
            await RatingsCog.import_rating(ctx.author.id, row)

        await ctx.send(f"Imported ratings successfully for user <@{ctx.message.author.id}>.")

    @staticmethod
    async def import_rating(user_id: int, row):
        """
        Import a single rating.
        """

        score = int(row["Rating"])

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
    await bot.add_cog(RatingsCog(bot))
