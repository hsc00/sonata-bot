from API.genius_search import *
from API.search_lastfm import get_lastfm_track
import time

def setup(bot):
    @bot.command(name='genius')
    async def genius(ctx):
        async with ctx.message.channel.typing():
            await check_samples(ctx.message)
            time.sleep(5)

async def check_samples(message):
    track_name = "The Story of OJ"
    artist_name = "Jay Z"
    related_titles = get_sampled_song_titles(track_name, artist_name)
    print(related_titles)