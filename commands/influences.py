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
            #await ctx.send(result)
        time.sleep(5)

    @bot.command(name='inf')
    async def inf(ctx):
        artist = ' '.join(ctx.message.content.split(' ')[1:]) if len(ctx.message.content.split(' ')) > 1 else None
        if not artist:
            await ctx.send("Please provide an artist name.")
            return
        
        async with ctx.message.channel.typing():
            result = await fetch_artist_data(artist, 'influences')
            #await ctx.send(result)
        time.sleep(5)

async def fetch_artist_data(artist, list_type):
    cached_data = load_from_cache(artist)
    if cached_data and list_type in cached_data:
        result = f"{list_type.capitalize()} for {artist} loaded from cache:\n"
        result += json.dumps(cached_data[list_type], indent=4)
    else:
        data_saved = False
        list_id = 'influencers-list' if list_type == 'influences' else 'followers-list'
        names = get_list(artist.replace(" ", "+"), list_id)
        if save_to_cache(artist, list_type, names):
            data_saved = True
        if data_saved:
            result = f"{list_type.capitalize()} for {artist} saved to cache:\n"
            result += json.dumps(names, indent=4)
        else:
            result = f"No data found for {artist}, nothing was saved to cache."
