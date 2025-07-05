import re

from discord.ext import commands
from peewee import fn

from api.last_fm import get_last_played
from core.errors import NoRatingsFound, NoLastFMUsername, InvalidUserMention
from database import UserInfo, AlbumIndex
from core.utils import paginate_embeds
from core.embeds import *


class ArtistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ar"])
    async def artist_ratings(self, ctx: commands.Context, *, query: Optional[str] = None):
        """
        Get the ratings for a given artist.
        """

        if query is None:
            user_id = str(ctx.message.author.id)
            user = UserInfo.get_or_none(UserInfo.user_id == user_id)
            last_fm_username = user.lastfm_username if user else None

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
            # Fetch user ID from mention if provided
            user_mention = re.search(r"<@!?(\d+)>", query)

            if user_mention:
                user_id = user_mention.group(1)
                artist_query = query.replace(f"<@{user_id}>", "").strip()

            else:
                user_id = ctx.message.author.id
                artist_query = query.strip()

        ratings = (
            Rating
            .select()
            .join(Album)
            .join(AlbumIndex, on=(Album.id == AlbumIndex.rowid))
            .where(
                (Rating.user == user_id) &
                (AlbumIndex.artist.match(artist_query))
            )
            .order_by(Rating.score.desc())
            .limit(100)
        )

        if len(ratings) == 0:
            raise NoRatingsFound(artist_query)

        embed = artist_ratings_embed(ratings, ratings[0].album.artist, ctx.message.author)

        await ctx.send(embed=embed)

    @commands.command(aliases=["bra"])
    async def best_rated_artists(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
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

        user_id = None

        if query:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                raise InvalidUserMention(query)

            user_id = match.group(1)

            best_rated_artists = best_rated_artists.where(Rating.user == user_id)

        if not best_rated_artists:
            raise NoRatingsFound()

        user_name = (await ctx.guild.fetch_member(int(user_id))).display_name

        view, pages = paginate_embeds(
            best_rated_artists,
            best_rated_artists_embed,
            per_page=10,
            server_name=ctx.guild.name,
            user_name=user_name,
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.command(aliases=["mra"])
    async def most_rated_artists(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
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

        if query:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                await ctx.send("Please provide a valid user mention.")

                return

            user_id = match.group(1)
            user_name = (await ctx.guild.fetch_member(int(user_id))).display_name
            most_rated_artists = most_rated_artists.where(Rating.user == user_id)

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
