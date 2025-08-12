from .releases import ReleasesCog


async def setup(bot) -> None:
    await bot.add_cog(ReleasesCog(bot))
