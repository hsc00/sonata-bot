from discord.ext import commands

from .releases import ReleasesCog


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReleasesCog(bot))
