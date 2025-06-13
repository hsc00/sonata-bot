from .users import UsersCog

async def setup(bot):
    await bot.add_cog(UsersCog(bot))