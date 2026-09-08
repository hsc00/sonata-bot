from __future__ import annotations

import contextlib
import csv
import html
import logging
import re
from typing import Literal

import discord
import requests
from api.rym import fetch_rym_user_info
from core.constants import (
    BAYESIAN_CONFIDENCE,
    BAYESIAN_PRIOR,
    RATING_SCORE_MAX,
    RATING_SCORE_MIN,
)
from core.embeds import (
    EmbedBuilder,
    comparison_embed,
    diff_embed,
    glazers_haters_rank_view,
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
from core.utils import create_rym_user_url, get_user_display_names, store_album
from database import Album, Rating, UserInfo
from discord import Message, app_commands
from discord.ext import commands
from peewee import IntegrityError, fn

logger = logging.getLogger(__name__)


class UsersCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def _build_rym_embed(
        rym_username: str,
        rym_info: dict,
    ) -> discord.Embed:
        url = create_rym_user_url(rym_username)
        title = rym_info.get("title") or f"RYM User: {rym_username}"
        snippet = rym_info.get("snippet", "")
        thumbnail = rym_info.get("thumbnail")

        embed = (
            EmbedBuilder()
            .with_title(title)
            .with_description(snippet or " ")
            .with_url(url)
            .build()
        )

        if thumbnail:
            with contextlib.suppress(discord.HTTPException):
                embed.set_thumbnail(url=thumbnail)

        return embed

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author == self.bot.user:
            return

        user_url_pattern = re.compile(
            r"https?://(?:www\.)?rateyourmusic\.com/~([^/?#]+)",
        )

        if not (matches := user_url_pattern.search(message.content)):
            return

        rym_username = matches.group(1)
        user_info = UserInfo.get_or_none(
            UserInfo.rym_username == rym_username,
        )

        if user_info:
            discord_user = None

            if message.guild:
                discord_user = message.guild.get_member(int(user_info.user_id))

            if discord_user is None:
                with contextlib.suppress(discord.HTTPException):
                    discord_user = await self.bot.fetch_user(int(user_info.user_id))

            if discord_user:
                average_score = (
                    Rating.select(fn.AVG(Rating.score).alias("average_rating"))
                    .where(Rating.user == user_info.user_id)
                    .scalar()
                )

                releases_rated = (
                    Rating.select(fn.COUNT(Rating.id).alias("rating_count"))
                    .where(Rating.user == user_info.user_id)
                    .scalar()
                )

                artists_rated = (
                    Rating.select(Rating.album, Album.artist)
                    .join(Album, on=(Rating.album == Album.id))
                    .where(Rating.user == user_info.user_id)
                    .group_by(Album.artist)
                ).count()

                rating_distribution = (
                    Rating.select(Rating.score, fn.COUNT(Rating.id).alias("count"))
                    .where(Rating.user == user_info.user_id)
                    .group_by(Rating.score)
                    .order_by(Rating.score.asc())
                )

                distribution_dict = {
                    row.score: row.count for row in rating_distribution
                }

                embed = profile_embed(
                    discord_user,
                    average_score,
                    releases_rated,
                    artists_rated,
                    distribution_dict,
                    rym_username=rym_username,
                )

                await message.channel.send(embed=embed)
                return

        rym_info = await fetch_rym_user_info(rym_username)

        if rym_info:
            embed = self._build_rym_embed(rym_username, rym_info)
            await message.channel.send(embed=embed)

        else:
            await message.channel.send(
                content=f"💔 No RateYourMusic profile found for **{rym_username}**."
            )

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

    @commands.hybrid_command(name="ratingsglazers", aliases=["rg"])
    async def ratings_glazers(self, ctx: commands.Context) -> None:
        """Get a ranking of users by their Bayesian average rating score."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        global_avg = (
            Rating.select(fn.AVG(Rating.score))
            .where(Rating.user.in_(guild_member_ids))
            .scalar()
        )
        if global_avg is None:
            global_avg = BAYESIAN_PRIOR

        rows = (
            Rating.select(
                Rating.user,
                fn.AVG(Rating.score).alias("average_score"),
                fn.COUNT(Rating.id).alias("rating_count"),
            )
            .where(Rating.user.in_(guild_member_ids))
            .group_by(Rating.user)
        )

        users_with_bayesian = []

        for row in rows:
            bayesian_avg = (
                row.rating_count * row.average_score + BAYESIAN_CONFIDENCE * global_avg
            ) / (row.rating_count + BAYESIAN_CONFIDENCE)
            row.bayesian_avg = bayesian_avg
            users_with_bayesian.append(row)

        sorted_users = sorted(
            users_with_bayesian,
            key=lambda row: row.bayesian_avg,
            reverse=True,
        )

        if not sorted_users:
            raise NoRatingsFoundError

        view = glazers_haters_rank_view(
            sorted_users,
            f"{ctx.guild.name} Glazers",
        )

        await ctx.send(embed=view.pages[0], view=view)

    @commands.hybrid_command(name="ratingshaters", aliases=["rh"])
    async def ratings_haters(self, ctx: commands.Context) -> None:
        """Get a ranking of users by their Bayesian average rating score."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        global_avg = (
            Rating.select(fn.AVG(Rating.score))
            .where(Rating.user.in_(guild_member_ids))
            .scalar()
        )
        if global_avg is None:
            global_avg = BAYESIAN_PRIOR

        rows = (
            Rating.select(
                Rating.user,
                fn.AVG(Rating.score).alias("average_score"),
                fn.COUNT(Rating.id).alias("rating_count"),
            )
            .where(Rating.user.in_(guild_member_ids))
            .group_by(Rating.user)
        )

        users_with_bayesian = []

        for row in rows:
            bayesian_avg = (
                row.rating_count * row.average_score + BAYESIAN_CONFIDENCE * global_avg
            ) / (row.rating_count + BAYESIAN_CONFIDENCE)
            row.bayesian_avg = bayesian_avg
            users_with_bayesian.append(row)

        sorted_users = sorted(
            users_with_bayesian,
            key=lambda row: row.bayesian_avg,
            reverse=False,
        )

        if not sorted_users:
            raise NoRatingsFoundError

        view = glazers_haters_rank_view(
            sorted_users,
            f"{ctx.guild.name} Haters",
        )

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

    @commands.hybrid_command(
        name="compare",
        aliases=["c"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(user="User to compare ratings with")
    async def compare(
        self,
        ctx: commands.Context,
        user: discord.User | discord.Member | None = None,
    ) -> None:
        """Compare your ratings with another user."""
        other_user_id = None

        if user is not None:
            other_user_id = str(user.id)

        elif ctx.message:
            content = ctx.message.content
            parts = content.split(maxsplit=1)
            if len(parts) == 2:
                arg = parts[1].strip()
                match = re.match(r"<@!?(\d+)>", arg)
                if match:
                    other_user_id = match.group(1)
                elif arg.isdigit():
                    other_user_id = arg

        if not other_user_id:
            raise InvalidUserMentionError

        user_id = str(ctx.author.id)

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
        )

        ratings = [
            row
            for row in common_ratings.dicts()
            if (row["score1"] - row["score2"]) != 0
        ]

        if not ratings:
            await ctx.send("💔 No ratings in common found.")

            return

        view, pages = paginate_embeds(ratings, comparison_embed, per_page=5)

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="diff",
        aliases=["d"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(user="User to compare against")
    async def diff(
        self,
        ctx: commands.Context,
        user: discord.User | discord.Member | None = None,
    ) -> None:
        """Show releases you've rated that another user hasn't."""
        other_user_id = None

        if user is not None:
            other_user_id = str(user.id)

        elif ctx.message:
            content = ctx.message.content
            parts = content.split(maxsplit=1)
            if len(parts) == 2:
                arg = parts[1].strip()
                match = re.match(r"<@!?(\d+)>", arg)
                if match:
                    other_user_id = match.group(1)
                elif arg.isdigit():
                    other_user_id = arg

        if not other_user_id:
            await ctx.send("Please mention a user or provide their user ID.")

            return

        user_id = str(ctx.author.id)

        other_ratings = Rating.select(Rating.album).where(Rating.user == other_user_id)

        diff_ratings = (
            Rating.select(
                Rating.album, Rating.score.alias("score1"), Album.title, Album.artist
            )
            .join(Album, on=(Rating.album == Album.id))
            .where(Rating.user == user_id)
            .where(Rating.album.not_in(other_ratings))
            .order_by(Rating.score.desc())
        )

        ratings = list(diff_ratings.dicts())

        if not ratings:
            await ctx.send("💔 No unique ratings found.")

            return

        view, pages = paginate_embeds(
            [{"user1": user_id, "user2": other_user_id, **r} for r in ratings],
            diff_embed,
            per_page=10,
        )

        await ctx.send(embed=pages[0], view=view)

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

        user_info = UserInfo.get_or_none(UserInfo.user_id == str(user.id))
        rym_username = user_info.rym_username if user_info else None

        embed = profile_embed(
            user,
            average_score,
            releases_rated,
            artists_rated,
            distribution_dict,
            rym_username=rym_username,
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
