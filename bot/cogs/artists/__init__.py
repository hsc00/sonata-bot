from .artists import ArtistCog

async def setup(bot):
    await bot.add_cog(ArtistCog(bot))