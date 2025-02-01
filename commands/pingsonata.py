def setup(bot):
    @bot.command(name='pingsonata')
    async def pingsonata(ctx):
        await ctx.send("pong")