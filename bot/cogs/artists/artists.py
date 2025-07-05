import re

from discord.ext import commands
from peewee import fn

from api.last_fm import get_last_played
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
            last_fm_username = UserInfo.get_or_none(str(ctx.message.author.id)).lastfm_username

            if last_fm_username is None:
                await ctx.send(
                    "❌ No last.fm username set. Please provide a search term or set your last.fm username by running `!set_lastfm <username>`.")

                return None

            _, artist_name, _ = get_last_played(last_fm_username)
            user_id = ctx.message.author.id

            if not artist_name:
                await ctx.send(
                    "Could not retrieve the last played artist. Please provide a search term."
                )

                return None

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
            await ctx.send(f'❌ No ratings exist for "{artist_query}".')

            return None

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

        if query:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                await ctx.send("❌ Please provide a valid user mention.")

                return

            user_id = match.group(1)

            best_rated_artists = best_rated_artists.where(Rating.user == user_id)

        if not best_rated_artists:
            await ctx.send("❌ No ratings exist for any artists.")

            return

        view, pages = paginate_embeds(
            best_rated_artists,
            best_rated_artists_embed,
            per_page=10,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)

    @commands.command(aliases=["mra"])
    async def most_rated_artists(self, ctx: commands.Context, *, query: Optional[str] = None) -> None:
        """
        Get the most rated artists.
        """

        user_id = None

        most_rated_artists = (
            Album
            .select(Album.artist, fn.COUNT(Rating.id).alias('rating_count'))
            .join(Rating)
            .group_by(Album.artist)
            .order_by(fn.COUNT(Rating.id).desc())
            .limit(100)
        )

        if query:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                await ctx.send("Please provide a valid user mention.")

                return

            user_id = match.group(1)

            most_rated_artists = most_rated_artists.where(Rating.user == user_id)

        if not most_rated_artists:
            await ctx.send("No ratings exist for any artists.")

            return

        view, pages = paginate_embeds(
            most_rated_artists,
            most_rated_artists_embed,
            per_page=10,
            user_id=user_id,
            server_name=ctx.guild.name
        )

        await ctx.send(embed=pages[0], view=view)
