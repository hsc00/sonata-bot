from __future__ import annotations

import csv
import html
import logging
import re
from typing import Literal

import discord
import requests
from core.constants import RATING_SCORE_MAX, RATING_SCORE_MIN
from core.decorators import disabled
from core.embeds import (
    comparison_embed,
    paginate_embeds,
    profile_embed,
    ratings_rank_view,
    users_list_embed,
)
from core.errors import (
    InvalidUserMentionError,
    NoFileAttachedError,
    NoRatingsFoundError,
    RatingsImportFailedError,
    SonataError,
)
from core.utils import get_user_display_names, store_album
from database import Album, Rating, UserInfo
from discord import app_commands
from discord.ext import commands
from peewee import IntegrityError, fn

logger = logging.getLogger(__name__)


class UsersCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="setrym",
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def set_rym(self, ctx: commands.Context, *, username: str | None) -> None:
        """Set your RYM username."""
        if not username:
            await ctx.send(
                "Please provide a [RateYourMusic](https://rateyourmusic.com/) username."
            )

            return

        user_info, created = UserInfo.get_or_create(
            user_id=str(ctx.author.id),
            defaults={"rym_username": username},
        )

        if not created:
            user_info.rym_username = username
            user_info.save()

        await ctx.send(f"Your RateYourMusic username has been set to **{username}**.")

    @commands.hybrid_command(
        name="setlastfm",
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
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

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

    @commands.hybrid_command(name="users")
    async def users_list(self, ctx: commands.Context) -> None:
        """List all users who have set their RYM username."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        users = (
            UserInfo.select()
            .where(UserInfo.rym_username.is_null(False))  # noqa: FBT003
            .order_by(UserInfo.rym_username)
        )

        users_list = list(users)

        if not users_list:
            await ctx.send("No users have set their RYM username yet.")

            return

        user_ids = {user.user_id for user in users_list}
        display_names = get_user_display_names(ctx.guild, user_ids)

        view, pages = paginate_embeds(
            users_list,
            users_list_embed,
            per_page=10,
            server_name=getattr(ctx.guild, "name", ""),
            user_display_names=display_names,
        )

        await ctx.send(embed=pages[0], view=view)

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
        user: discord.User | discord.Member | None = None,
    ) -> None:
        if user is None:
            user = ctx.author

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

        rating_distribution = (
            Rating.select(Rating.score, fn.COUNT(Rating.id).alias("count"))
            .where(Rating.user == user.id)
            .group_by(Rating.score)
            .order_by(Rating.score.asc())
        )

        distribution_dict = {row.score: row.count for row in rating_distribution}

        embed = profile_embed(
            user,
            average_score,
            releases_rated,
            artists_rated,
            distribution_dict,
        )

        await ctx.send(embed=embed)

    @commands.command(name="importratings", aliases=["i"])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def import_ratings(self, ctx: commands.Context) -> None:
        """Import ratings from RYM."""
        if not ctx.message.attachments:
            raise NoFileAttachedError

        attachment_url = ctx.message.attachments[0].url
        response = requests.get(attachment_url, timeout=10)

        if not response.ok:
            raise RatingsImportFailedError

        try:
            rows = list(csv.DictReader(response.text.splitlines()))

            if not rows:
                await ctx.send("The CSV file appears to be empty.")
                return

            headers = rows[0].keys()

            if "Release_Date" in headers:
                format_type = "rym"
                normalize = self._normalize_rym_row

            elif "Date Rated" in headers:
                format_type = "aoty"
                normalize = self._normalize_aoty_row

            else:
                await ctx.send(
                    "❌ Unknown CSV format. Expected RYM or AOTY export file."
                )

                return

            # Clean existing ratings for the user
            Rating.delete().where(Rating.user == ctx.author.id).execute()

            async with ctx.typing():
                imported = 0
                skipped = 0

                for row in rows:
                    try:
                        normalized = normalize(row)

                        if normalized["score"] == 0:
                            skipped += 1
                            continue

                        await self.import_rating(ctx.author.id, normalized)
                        imported += 1

                    except Exception:  # noqa: BLE001
                        skipped += 1
                        continue

                await ctx.send(
                    content=f"✅ Imported **{imported}** ratings from {format_type.upper()} export"
                    f" for user {ctx.message.author.name}."
                    + (f" Skipped **{skipped}** rows." if skipped else ""),
                )

        except Exception as e:
            raise RatingsImportFailedError from e

    @staticmethod
    def _normalize_rym_row(row: dict) -> dict:
        first_name = row.get(" First Name") or row.get(" First Name localized") or ""
        last_name = row.get("Last Name") or row.get("Last Name localized") or ""
        artist = html.unescape(f"{first_name + ' ' if first_name else ''}{last_name}")
        review = row.get("Review") or row.get(" Review") or None
        review = html.unescape(review) if review else None

        return {
            "title": html.unescape(row.get("Title", "")),
            "artist": artist,
            "score": int(row.get("Rating", 0)),
            "year": int(row.get("Release_Date") or "0"),
            "review": review,
        }

    @staticmethod
    def _normalize_aoty_row(row: dict) -> dict:
        raw_score = int(row.get("Rating", 0))
        score = max(RATING_SCORE_MIN, min(RATING_SCORE_MAX, round(raw_score / 10)))

        return {
            "title": row.get("Album", ""),
            "artist": row.get("Artist", ""),
            "score": score,
            "year": int(row.get("Year") or "0"),
            "review": None,
        }

    @staticmethod
    async def import_rating(user_id: int, row: dict) -> None:
        """Import a single normalized rating row."""
        score = int(row["score"])

        # Skip wishlisted albums
        if score == 0:
            return

        if score < RATING_SCORE_MIN or score > RATING_SCORE_MAX:
            message = f"Score must be between {RATING_SCORE_MIN} and {RATING_SCORE_MAX}"
            raise ValueError(message)

        title = html.unescape(row["title"])
        artist = html.unescape(row["artist"])
        release_year = int(row.get("year") or "0")

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
            rating, created = Rating.get_or_create(
                user=user_id,
                album=album,
                defaults={"score": score, "review": row.get("review")},
            )

            if not created:
                rating.score = score
                rating.review = row.get("review")
                rating.save()

        except IntegrityError:
            logger.exception(
                f"Failed to create rating for {album.title} by {album.artist} ({album.release_year})"
            )

    @commands.hybrid_command(
        name="sync",
        description="Sync slash commands to the guild or globally",
    )
    async def sync(
        self,
        ctx: commands.Context,
        scope: Literal["global", "guild"] | None = "guild",
    ) -> None:
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

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
