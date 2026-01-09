from __future__ import annotations

import csv
import html
import re
from typing import Literal
from venv import logger

import discord
import requests
from core.decorators import disabled
from core.embeds import comparison_embed, profile_embed, ratings_rank_view
from core.errors import (
    InvalidUserMentionError,
    NoFileAttachedError,
    NoRatingsFoundError,
    RatingsImportFailedError,
)
from core.utils import store_album
from database import Album, Rating, UserInfo
from discord import app_commands
from discord.ext import commands
from peewee import IntegrityError, fn


class UsersCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @disabled()
    @commands.command()
    async def set_rym(self, ctx: commands.Context, username: str) -> None:
        """Set your RYM username."""
        if not username:
            await ctx.send(
                "Please provide a [RateYourMusic](https://rateyourmusic.com/) username."
            )

            return

        UserInfo.create(user_id=ctx.author.id, rym_username=username)

        await ctx.send(f"Your RateYourMusic username has been set to **{username}**.")

    @commands.hybrid_command(
        name="setlastfm",
        aliases=["set_lastfm"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def set_lastfm(self, ctx: commands.Context, *, username: str | None) -> None:
        """Set your last.fm username."""
        if not username:
            await ctx.send("Please provide a [last.fm](https://www.last.fm/) username.")

            return

        user_info, created = UserInfo.get_or_create(
            user_id=str(ctx.author.id),
            defaults={"lastfm_username": username},
        )

        if not created:
            user_info.lastfm_username = username
            user_info.save()

        await ctx.send(f"Your last.fm username has been set to **{username}**.")

    @commands.hybrid_command(name="ratingsrank", aliases=["rr"])
    async def ratings_rank(self, ctx: commands.Context) -> None:
        """Get a ranking of users by their number of ratings."""
        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        ratings = (
            Rating.select(Rating.user, fn.COUNT(Rating.id).alias("rating_count"))
            .where(Rating.user.in_(guild_member_ids))
            .group_by(Rating.user)
            .order_by(fn.COUNT(Rating.id).desc())
            .limit(100)
        )

        if not ratings:
            raise NoRatingsFoundError

        view = ratings_rank_view(ctx.guild.name, ratings)

        await ctx.send(embed=view.pages[0], view=view)

    @disabled()
    @commands.command(aliases=["c"])
    async def compare(self, ctx: commands.Context, *, query: str | None = None) -> None:
        """Compare your ratings with another user."""
        if not query:
            raise InvalidUserMentionError

        match = re.match(r"<@!?(\d+)>", query)

        if not match:
            raise InvalidUserMentionError(query)

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
                Album.artist,
            )
            .join(Album, on=(r1.album == Album.id))
            .switch(r1)
            .join(r2, on=(r1.album == r2.album))
            .where(
                (r1.user == user_id) & (r2.user == other_user_id),
            )
            .order_by(r1.score - r2.score)
            .limit(100)
        )

        if common_ratings.limit(1).first() is None:
            await ctx.send("💔 No ratings in common found.")

            return

        # Compare ratings and create an embed
        embed = comparison_embed(list(common_ratings.dicts()))

        await ctx.send(embed=embed)

    @commands.hybrid_command(with_app_command=True)
    async def profile(
        self,
        ctx: commands.Context,
        user: discord.User | None = None,
    ) -> None:
        user = ctx.author if user is None else user
        average_score = (
            Rating.select(fn.AVG(Rating.score).alias("average_rating"))
            .where(Rating.user == user.id)
            .scalar()
        )

        releases_rated = (
            Rating.select(fn.COUNT(Rating.id).alias("rating_count"))
            .where(Rating.user == user.id)
            .scalar()
        )

        artists_rated = (
            Rating.select(Rating.album, Album.artist)
            .join(Album, on=(Rating.album == Album.id))
            .where(Rating.user == user.id)
            .group_by(Album.artist)
        ).count()

        embed = profile_embed(user, average_score, releases_rated, artists_rated)

        await ctx.send(embed=embed)

    @commands.command(name="import", aliases=["i"])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def import_ratings(self, ctx: commands.Context) -> None:
        """Import ratings from RYM."""
        if not ctx.message.attachments:
            raise NoFileAttachedError

        attachment_url = ctx.message.attachments[0].url
        response = requests.get(attachment_url)

        if response.headers.get("Content-Type") != "text/csv":
            raise RatingsImportFailedError("The uploaded file is not a CSV file.")

        if not response.ok:
            raise RatingsImportFailedError

        try:
            # Clean existing ratings for the user
            Rating.delete().where(Rating.user == ctx.author.id).execute()

            rows = list(csv.DictReader(response.text.splitlines()))

            async with ctx.typing():
                for row in rows:
                    await self.import_rating(ctx.author.id, row)

                await ctx.send(
                    content=f"✅ Imported ratings successfully for user {ctx.message.author.name}.",
                )

        except Exception as e:
            raise RatingsImportFailedError from e

    @staticmethod
    async def import_rating(user_id: int, row) -> None:
        """Import a single rating."""
        score = int(row["Rating"])

        # Skip wishlisted albums
        if score == 0:
            return

        if score < 1 or score > 10:
            raise ValueError("Score must be between 1 and 10")

        title = html.unescape(row["Title"])

        first_name = row[" First Name"] or None
        last_name = row["Last Name"]
        artist = html.unescape(f"{first_name + " " if first_name else ""}{last_name}")
        release_year = int(row.get("Release_Date") or "0")

        # Search for the album in the database
        try:
            album = Album.get(
                Album.title == title,
                fn.COALESCE(Album.album_artist, Album.artist) == artist,
                Album.release_year == release_year,
            )

        # If the album is not found, create it
        except Album.DoesNotExist:
            album = Album(
                title=title,
                artist=artist,
                album_artist=artist,
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

        except IntegrityError as e:
            logger.error(e, album.title, album.artist, album.release_year)

    @commands.hybrid_command(
        name="sync",
        description="Sync slash commands to the guild or globally",
    )
    async def sync(
        self,
        ctx: commands.Context,
        scope: Literal["global", "guild"] | None = "guild",
    ) -> None:
        if ctx.author.id not in (self.bot.owner_id, 207090194006933505):
            await ctx.send(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        if scope == "guild":
            guild = discord.Object(id=ctx.guild.id)
            self.bot.tree.copy_global_to(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
            await ctx.send(
                f"Synced {len(synced)} command(s) to this guild.",
                ephemeral=True,
            )

        elif scope == "global":
            synced = await self.bot.tree.sync()
            await ctx.send(f"Globally synced {len(synced)} command(s).", ephemeral=True)

        else:
            await ctx.send("Invalid scope. Use 'guild' or 'global'.", ephemeral=True)
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UsersCog(bot))
