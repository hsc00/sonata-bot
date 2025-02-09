import time
import discord
from collections import defaultdict
from views import Paginator
from API.album_cache import *
from API.search_lastfm import get_lastfm_track
from API.rym_search import get_rym_rating

def setup(bot):
    @bot.command(name='ratingchanges')
    async def ratingchanges(ctx):
        async with ctx.message.channel.typing():
            await get_rating(ctx.message)
            time.sleep(5)

    @bot.command(name='rc')
    async def rc(ctx):
        async with ctx.message.channel.typing():
            await get_rating(ctx.message)
            time.sleep(5)

async def get_rating(message):
    release_query = ' '.join(message.content.split(' ')[1:]) if len(message.content.split(' ')) > 1 else None
    if not release_query:
        release_query = get_lastfm_track(message.author.id, 'release')
        if release_query is None:
            await message.channel.send('Please provide an artist or use `!setfm` to set your last.fm account.')
            return
    release = get_album_from_cache(release_query)
    if release:
        release_name = f'{release["artist_name"]} - {release["release_name"]}'
        link = release['link']
        release_rating_history = get_rym_rating(release_name)
        if len(release_rating_history['rating_history']) > 1:
            release_changes = format_release_changes(release_rating_history)
            if release_changes:
                pages = [release_changes[i:i + 10] for i in range(0, len(release_changes), 10)]
                embeds = []
                embed_title = f"{release_name}"
                for i, page in enumerate(pages):
                    embed_description = "\n".join(page)
                    # Determine the color based on the latest rating change
                    newest_rating = float(release_rating_history['rating_history'][-1]['value'])
                    previous_rating = float(release_rating_history['rating_history'][-2]['value'])
                    embed_color = discord.Color.green() if newest_rating > previous_rating else discord.Color.red()
                    
                    embed = discord.Embed(title=embed_title, description=embed_description, url=link, color=embed_color)
                    if release['album_cover_url']:
                        embed.set_thumbnail(url=release['album_cover_url'])
                    elif release['rym_cover_url']:
                        embed.set_thumbnail(url=release['rym_cover_url'])
                    embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i + 1}/{len(pages)}")
                    embeds.append(embed)
                sent_message = await message.channel.send(embed=embeds[0])
                view = Paginator(embeds)
                await sent_message.edit(embed=embeds[0], view=view)
            else:
                await message.channel.send(f"The data couldn't be formatted correctly.")
        else:
            await message.channel.send(f"No rating changes found for **{release_name}**")
    else:
        await message.channel.send(f'No previous ratings found for **{release_query.title()}**. Please use `!album` or `!ab` to add the release.')

def format_release_changes(release_changes):
    formatted_output = []
    release_year = release_changes.get('release_year', 'N/A')
    sorted_rating_history = sorted(release_changes['rating_history'], key=lambda x: x['timestamp'], reverse=True)

    for idx in range(len(sorted_rating_history)):
        date = datetime.datetime.fromisoformat(sorted_rating_history[idx]['timestamp']).strftime('%d-%m-%Y')
        rating_value = sorted_rating_history[idx]['value']
        rating_count = release_changes['rating_count_history'][idx].get('count', 'N/A')
        year_position = release_changes['year_position_history'][idx].get('position', 'N/A')
        all_time_position = release_changes['all_time_position_history'][idx].get('position', 'N/A')

        formatted_data = f"{date}\n**{rating_value}** ⭐ from **{rating_count}** ratings\n**#{year_position}** of [{release_year}](https://rateyourmusic.com/charts/top/album/{release_year})"
        if all_time_position:
            formatted_data += f", **#{all_time_position}** [overall](https://rateyourmusic.com/charts/top/album/all-time/)"
        formatted_output.append('')
        formatted_output.append(formatted_data)

    return formatted_output

