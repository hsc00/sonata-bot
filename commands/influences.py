from API.influences_search import *
import time

def setup(bot):
    @bot.command(name='influences')
    async def influences(ctx):
        artist = ' '.join(ctx.message.content.split(' ')[1:]) if len(ctx.message.content.split(' ')) > 1 else None
        if not artist:
            await ctx.send("Please provide an artist name.")
            return
        async with ctx.message.channel.typing():
            result = await fetch_artist_data(artist, 'influences')
            if result:
                print(result)
            else:
                await ctx.send("No data found.")
        time.sleep(5)
    @bot.command(name='inf')
    async def inf(ctx):
        artist = ' '.join(ctx.message.content.split(' ')[1:]) if len(ctx.message.content.split(' ')) > 1 else None
        if not artist:
            await ctx.send("Please provide an artist name.")
            return
        async with ctx.message.channel.typing():
            result = await fetch_artist_data(artist, 'influences')
            if result:
                print(result)
            else:
                await ctx.send("No data found.")
        time.sleep(5)


async def fetch_artist_data(artist, list_type):
    cached_data = load_from_cache(artist)
    if cached_data and list_type in cached_data:
        return cached_data[list_type]
    else:
        data = get_lists(artist.replace(" ", "+"))
        save_to_cache(artist, data)
        return data[list_type]
