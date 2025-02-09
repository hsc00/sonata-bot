import time
import discord
from collections import defaultdict
from views import Paginator
from API.album_cache import *
from API.search_lastfm import get_lastfm_track
from API.rym_search import get_rym_rating

def setup(bot):
    @bot.command(name='ratingchanges')
    async def wholikesartist(ctx):
        async with ctx.message.channel.typing():
            await get_rating(ctx.message)
            pass
            time.sleep(5)

    @bot.command(name='rc')
    async def wla(ctx):
        await get_rating(ctx.message)
        pass
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
        if release_rating_history:
            release_changes = format_release_changes(release_rating_history)
            if release_changes:
                pages = [release_changes[i:i + 10] for i in range(0, len(release_changes), 10)]
                embeds = []
                embed_title = f"{release_name}"
                for i, page in enumerate(pages):
                    embed_description = "\n".join(page)
                    embed = discord.Embed(title=embed_title, description=embed_description, url=link)
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
                await message.channel.send(f"No rating changes found for **{release_name}**")
        else:
            await message.channel.send(f"No rating changes found for **{release_name}**")
    else:
        await message.channel.send(f'No previous ratings found for **{release_query.title()}**. Please use `!album` or `!ab` to add the release.')

def format_release_changes(release_changes):
    formatted_changes = defaultdict(lambda: defaultdict(list))
    for key, changes in release_changes.items():
        for change in changes:
            if 'timestamp' in change:
                date = datetime.datetime.fromisoformat(change['timestamp']).strftime('%d-%m-%Y')
                formatted_changes[date][key].append(change)
            else:
                return None

    formatted_output = []
    more_than_one_rating = sum(len(data['rating_history']) for data in formatted_changes.values() if 'rating_history' in data) > 1

    if more_than_one_rating:
        for date, data in formatted_changes.items():
            ratings = []
            counts = []
            year_positions = []
            all_time_positions = []

            if 'rating_history' in data:
                ratings = [rh['value'] for rh in data['rating_history']]
            if 'rating_count_history' in data:
                counts = [ch['count'] for ch in data['rating_count_history'] if 'count' in ch]
            if 'year_position_history' in data:
                year_positions = [yh['position'] for yh in data['year_position_history']]
            if 'all_time_position_history' in data:
                all_time_positions = [pos['position'] for pos in data['all_time_position_history']]

            release_year = release_changes.get('release_year', 'N/A')

            for i in range(max(len(ratings), len(counts), len(year_positions), len(all_time_positions))):
                rating_value = ratings[i] if i < len(ratings) else 'N/A'
                rating_count = counts[i] if i < len(counts) else 'N/A'
                year_position = year_positions[i] if i < len(year_positions) and year_positions[i] is not None else None
                all_time_position = ', '.join([pos for pos in all_time_positions if pos]) if all_time_positions else None

                formatted_date_data = f"\n{date}\n**{rating_value}** ⭐ from **{rating_count}** ratings"
                if year_position:
                    formatted_date_data += f"\n**#{year_position}** of {release_year}"
                if all_time_position:
                    formatted_date_data += f", **#{all_time_position}** overall"

                formatted_date_data += "\n"

                formatted_output.append('')
                formatted_output.append(formatted_date_data.strip())

    return formatted_output if more_than_one_rating else None
