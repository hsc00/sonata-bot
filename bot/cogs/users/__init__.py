from discord.ext import commands

from .users import UsersCog


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UsersCog(bot))
