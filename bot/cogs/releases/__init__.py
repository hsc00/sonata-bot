from .releases import ReleasesCog

async def setup(bot):
    await bot.add_cog(ReleasesCog(bot))