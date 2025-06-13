import re

from discord.ext import commands
from peewee import fn

from api.last_fm import get_last_played
from database import UserInfo
from utils import make_rym_artist_url
from utils.embeds import *
from urllib.parse import quote


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
                await ctx.send('Please provide an artist or use `!setfm` to set your last.fm account.')

                return None

            artist = get_last_played(last_fm_username, "artist")

            if not artist:
                await ctx.send(
                    "Could not retrieve the last played album. Please provide a search term."
                )

                return None

        else:
            artist = query

        ratings = (
            Rating
            .select()
            .join(Album)
            .where((Album.artist == artist) & (Rating.user == str(ctx.message.author.id)))
            .order_by(Rating.score.desc())
        )

        if len(ratings) == 0:
            await ctx.send(f'No ratings exist for "{artist}".')

            return None

        embed = make_artist_ratings_embed(ratings, artist, ctx.message.author)

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
            .limit(10)
        )

        if query:
            match = re.match(r"<@!?(\d+)>", query)

            if not match:
                await ctx.send("Please provide a valid user mention.")

                return

            user_id = match.group(1)

            best_rated_artists = best_rated_artists.where(Rating.user == user_id)

        if not best_rated_artists:
            await ctx.send("No ratings exist for any artists.")

            return

        embed = make_best_rated_artists_embed(ctx.guild.name, best_rated_artists)

        await ctx.send(embed=embed)

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
            .limit(10)
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

        title = f"Artists with most ratings for user" if user_id else f"Artists with most ratings in {ctx.guild.name}"

        embed = discord.Embed(
            title=title,
            description="\n".join(
                f"{i}. [{row.artist}]({make_rym_artist_url(row.artist)}) (**{row.rating_count}** ratings)"
                for i, row in enumerate(most_rated_artists, start=1)
            ),
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)
