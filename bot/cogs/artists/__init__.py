from discord.ext import commands

from .artists import ArtistCog


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ArtistCog(bot))
