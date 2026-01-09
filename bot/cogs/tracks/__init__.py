from .tracks import TracksCog


async def setup(bot):
    await bot.add_cog(TracksCog(bot))
