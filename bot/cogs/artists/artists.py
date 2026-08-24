from __future__ import annotations

from typing import Any

import discord
from api.last_fm import get_last_played
from core.constants import (
    ARTIST_RATING_W1,
    ARTIST_RATING_W2,
    ARTIST_RATING_W3,
    RATINGS_MIN_THRESHOLD,
)
from core.embeds import (
    artist_ratings_embed,
    best_rated_artists_embed,
    most_rated_artists_embed,
    paginate_embeds,
    worst_rated_artists_embed,
)
from core.errors import NoLastFMUsernameError, NoRatingsFoundError, SonataError
from database import AlbumIndex, UserInfo
from database.models import Album, Rating
from discord import app_commands
from discord.ext import commands
from peewee import fn


class ArtistCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="artistratings",
        aliases=["ar"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def artist_ratings(
        self,
        ctx: commands.Context,
        user: discord.User | None = None,
        *,
        artist_name: str | None = None,
    ) -> None:
        """Get the ratings for a given artist."""
        if user is None:
            user_id = str(ctx.message.author.id)
            user_name = ctx.message.author.display_name

        else:
            user_id = str(user.id)
            user_name = user.display_name

        if artist_name is None:
            user_info = UserInfo.get_or_none(UserInfo.user_id == user_id)
            last_fm_username = user_info.lastfm_username if user_info else None

            if last_fm_username is None:
                raise NoLastFMUsernameError

            _, artist_name, _ = get_last_played(last_fm_username)
            user_id = ctx.message.author.id

            if not artist_name:
                await ctx.send(
                    "Could not retrieve the last played artist. Please provide a search term.",
                )

            artist_query = artist_name

        else:
            artist_query = artist_name

        artist = (
            AlbumIndex.select(
                AlbumIndex.artist,
                fn.COUNT(Rating.id).alias("rating_count"),
            )
            .join(Album, on=(AlbumIndex.rowid == Album.id))
            .join(Rating, on=((Rating.album == Album.id) & (Rating.user == user_id)))
            .where(AlbumIndex.match(f"artist:{artist_query}"))
            .group_by(AlbumIndex.artist)
            .order_by(fn.COUNT(Rating.id).desc())
            .first()
        )

        if not artist:
            raise NoRatingsFoundError(artist_query)

        ratings = (
            Rating.select()
            .join(Album)
            .where((Rating.user == user_id) & (Album.artist == artist.artist))
            .order_by(Rating.score.desc())
            .limit(100)
        )

        if len(ratings) == 0:
            raise NoRatingsFoundError(artist_query)
        view, pages = paginate_embeds(
            ratings,
            artist_ratings_embed,
            per_page=10,
            artist=artist.artist,
            user_name=user_name,
            average_score=sum(rating.score for rating in ratings) / len(ratings),
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="bestratedartists",
        aliases=["bra"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def best_rated_artists(
        self,
        ctx: commands.Context,
        user: discord.User | None = None,
    ) -> None:
        """Get the best rated artists."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        w1, w2, w3 = ARTIST_RATING_W1, ARTIST_RATING_W2, ARTIST_RATING_W3
        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        best_rated_artists = (
            Album.select(
                Album.artist,
                fn.AVG(Rating.score).alias("average_score"),
                fn.COUNT(fn.DISTINCT(Album.id)).alias("releases_count"),
            )
            .join(Rating)
            .where(Rating.user.in_(guild_member_ids))
            .group_by(Album.artist)
            .having(fn.COUNT(Rating.id) > RATINGS_MIN_THRESHOLD)
            .order_by(
                (
                    w1 * fn.AVG(Rating.score)
                    + w2 * fn.COUNT(Rating.id)
                    + w3 * fn.COUNT(fn.DISTINCT(Album.id)) * fn.AVG(Rating.score)
                ).desc(),
            )
            .limit(100)
        )

        user_name = None

        if user:
            user_id = user.id
            user_name = (await ctx.guild.fetch_member(int(user_id))).display_name

            best_rated_artists = best_rated_artists.where(Rating.user == user_id)

        if not best_rated_artists:
            raise NoRatingsFoundError

        view, pages = paginate_embeds(
            best_rated_artists,
            best_rated_artists_embed,
            per_page=10,
            server_name=getattr(ctx.guild, "name", ""),
            user_name=user_name,
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="worstratedartists",
        aliases=["wra"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def worst_rated_artists(
        self,
        ctx: commands.Context,
        user: discord.User | None = None,
    ) -> None:
        """Get the worst rated artists."""
        if ctx.guild is None:
            raise SonataError("This command can only be used in a guild.")

        w1, w2, w3 = ARTIST_RATING_W1, ARTIST_RATING_W2, ARTIST_RATING_W3
        guild_member_ids = {str(member.id) for member in ctx.guild.members}

        worst_rated_artists = (
            Album.select(
                Album.artist,
                fn.AVG(Rating.score).alias("average_score"),
                fn.COUNT(fn.DISTINCT(Album.id)).alias("releases_count"),
            )
            .join(Rating)
            .where(Rating.user.in_(guild_member_ids))
            .group_by(Album.artist)
            .having(fn.COUNT(Rating.id) > RATINGS_MIN_THRESHOLD)
            .order_by(
                (
                    w1 * fn.AVG(Rating.score)
                    + w2 * fn.COUNT(Rating.id)
                    + w3 * fn.COUNT(fn.DISTINCT(Album.id)) * fn.AVG(Rating.score)
                ).asc(),
            )
            .limit(100)
        )

        user_name = None

        if user:
            user_id = user.id
            user_name = (await ctx.guild.fetch_member(int(user_id))).display_name

            worst_rated_artists = worst_rated_artists.where(Rating.user == user_id)

        if not worst_rated_artists:
            raise NoRatingsFoundError

        view, pages = paginate_embeds(
            worst_rated_artists,
            worst_rated_artists_embed,
            per_page=10,
            server_name=getattr(ctx.guild, "name", ""),
            user_name=user_name,
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(
        name="mostratedartists",
        aliases=["mra"],
        with_app_command=True,
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def most_rated_artists(
        self,
        ctx: commands.Context[Any],
        user: discord.User | None = None,
    ) -> None:
        """Get the most rated artists."""
        most_rated_artists = (
            Album.select(Album.artist, fn.COUNT(Rating.id).alias("rating_count"))
            .join(Rating)
            .group_by(Album.artist)
            .order_by(fn.COUNT(Rating.id).desc())
            .limit(100)
        )

        user_name = None

        if user:
            user_name = user.display_name
            most_rated_artists = most_rated_artists.where(Rating.user == user.id)

        if not most_rated_artists:
            raise NoRatingsFoundError

        view, pages = paginate_embeds(
            most_rated_artists,
            most_rated_artists_embed,
            per_page=10,
            user_name=user_name,
            server_name=getattr(ctx.guild, "name", ""),
        )

        await ctx.send(embed=pages[0], view=view)
