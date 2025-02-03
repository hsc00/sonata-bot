import time
from API.artist_cache import *

def setup(bot):
    @bot.command(name='wholikedartist')
    async def wholiked(ctx):
        async with ctx.message.channel.typing():
            await who_liked_disliked_artist(ctx.message)
            pass
            time.sleep(5)

    @bot.command(name='wla')
    async def wl(ctx):
        await who_liked_disliked_artist(ctx.message)
        pass
        time.sleep(5)

async def who_liked_disliked_artist(message):
    likes = get_artist_from_cache()