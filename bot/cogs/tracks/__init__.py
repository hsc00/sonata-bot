from discord.ext import commands

from .tracks import TracksCog


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TracksCog(bot))
