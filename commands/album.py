from discord.ext import commands

def setup(bot):
    @bot.command(name='album')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def album(ctx):
        pass

    @bot.command(name='ab')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ab(ctx):
        pass
