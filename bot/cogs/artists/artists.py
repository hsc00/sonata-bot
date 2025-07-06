from discord.ext import commands
from discord.ext.commands import Greedy
from peewee import fn

from api.last_fm import get_last_played
from core.errors import NoRatingsFound, NoLastFMUsername
from database import UserInfo, AlbumIndex
from core.embeds import *


class ArtistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="artistratings", aliases=["ar"])
    async def artist_ratings(
            self,
            ctx: commands.Context,
            user: discord.User | None = None,
            *,
            artist_name: str | None = None,
    ):
        """
        Get the ratings for a given artist.
        """

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
                raise NoLastFMUsername()

            _, artist_name, _ = get_last_played(last_fm_username)
            user_id = ctx.message.author.id

            if not artist_name:
                await ctx.send(
                    "Could not retrieve the last played artist. Please provide a search term."
                )

            artist_query = artist_name

        else:
            artist_query = artist_name

        artist = (
            AlbumIndex
            .select(AlbumIndex.artist)
            .where(AlbumIndex.artist.match(artist_query))
            .group_by(AlbumIndex.artist)
            .first()
        )

        if not artist:
            raise NoRatingsFound(artist_query)

        ratings = (
            Rating
            .select()
            .join(Album)
            .where(
                (Rating.user == user_id) &
                (Album.artist == artist.artist)
            )
            .order_by(Rating.score.desc())
            .limit(100)
        )

        if len(ratings) == 0:
            raise NoRatingsFound(artist_query)

        embed = artist_ratings_embed(
            ratings,
            artist.artist,
            user_name
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bestratedartists", aliases=["bra"])
    async def best_rated_artists(
            self,
            ctx: commands.Context,
            user: discord.User | None = None
    ) -> None:
        """
        Get the best rated artists.
        """

        w1, w2, w3 = 14, 0.07, 0.1

        best_rated_artists = (
            Album
            .select(
                Album.artist,
                fn.AVG(Rating.score).alias('average_score'),
                fn.COUNT(fn.DISTINCT(Album.id)).alias('releases_count'),
            )
            .join(Rating)
            .group_by(Album.artist)
            .having(fn.COUNT(Rating.id) > 3)
            .order_by(
                (w1 * fn.AVG(Rating.score)
                 + w2 * fn.COUNT(Rating.id)
                 + w3 * fn.COUNT(fn.DISTINCT(Album.id)) * fn.AVG(Rating.score)
                 ).desc()
            )
            .limit(100)
        )

        user_name = None

        if user:
            user_id = user.id
            user_name = (await ctx.guild.fetch_member(int(user_id))).display_name

            best_rated_artists = best_rated_artists.where(Rating.user == user_id)

        if not best_rated_artists:
            raise NoRatingsFound()

        view, pages = paginate_embeds(
            best_rated_artists,
            best_rated_artists_embed,
            per_page=10,
            server_name=ctx.guild.name,
            user_name=user_name,
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(name="mostratedartists", aliases=["mra"])
    async def most_rated_artists(
            self,
            ctx: commands.Context,
            user: discord.User | None = None,
    ) -> None:
        """
        Get the most rated artists.
        """

        most_rated_artists = (
            Album
            .select(Album.artist, fn.COUNT(Rating.id).alias('rating_count'))
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
            raise NoRatingsFound()

        view, pages = paginate_embeds(
            most_rated_artists,
            most_rated_artists_embed,
            per_page=10,
            user_name=user_name,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)
