from typing import Optional

from discord.ext import commands
from peewee import fn

from database import UserInfo, Rating
from utils.embeds import make_ratings_rank_view


class UsersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def set_rym(self, ctx: commands.Context, username: str):
        """
        Set your RYM username.
        """

        UserInfo.create(user_id=ctx.author.id, rym_username=username)

        await ctx.send(f"Your RYM username has been set to **{username}**.")

    @commands.command()
    async def set_lastfm(self, ctx: commands.Context, *, username: Optional[str]):
        """
        Set your last.fm username.
        """

        if not username:
            await ctx.send("Please provide a last.fm username.")

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


async def setup(bot):
    await bot.add_cog(UsersCog(bot))
