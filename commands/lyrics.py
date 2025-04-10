import time
import re
from syncedlyrics import search
from API.spotify_search import *
from API.search_lastfm import get_lastfm_track

def setup(bot):
    @bot.command(name='lyrics')
    async def lyrics(ctx, *, track_name: str = None):
        async with ctx.message.channel.typing():
            await check_lyrics(ctx, track_name)
            time.sleep(5)

    @bot.command(name='lr')
    async def lr(ctx, *, track_name: str = None):
        async with ctx.message.channel.typing():
            await check_lyrics(ctx, track_name)
            time.sleep(5)

async def check_lyrics(ctx, track_name: str):
    source = "spotify"
    user_id = ctx.author.id
    timestamp = "00:00:00"
    if track_name is None: track_name = ""
    
    match = re.search(r'(\d{2}:\d{2}:\d{2}|\d{2}:\d{2})$', track_name)
    if match:
        timestamp = match.group()
        # Check if the timestamp is in the mm:ss format
        if re.match(r'\d{2}:\d{2}$', timestamp):
            # Add 00: to the timestamp to make it hh:mm:ss
            timestamp = f'00:{timestamp}'
        # Remove the timestamp from the track_name
        track_name = track_name[:match.start()].strip()
    # This checks if only the timestamp was send
    if track_name is None or track_name == "":
        # Spotify check
        currently_playing = await get_currently_playing(user_id)
        if currently_playing.get('timestamp'):
            timestamp = currently_playing.get('timestamp')
            track_name = currently_playing.get('artists') + " - " + currently_playing.get('track_name')
        # Last.fm check
        else:
            track_name = get_lastfm_track(user_id, 'track')
            source = "last.fm"
            if track_name is None:
                # Show Spotify error
                await ctx.reply(currently_playing.get('error', 'Weird exception, report to the owner 🚒'))
                return
                
    # Fetch synchronized lyrics
    synced_lyrics = search(track_name)
    if not synced_lyrics:
        await ctx.lyrics("No synchronized lyrics found 🤓☝️")
        return
    
    # Parse the timestamp (expected format: hh:mm:ss)
    input_timestamp = convert_timestamp_to_seconds(timestamp)

    # Split the lyrics into lines and extract timestamps
    lyrics_lines = synced_lyrics.split('\n')
    timestamps = extract_timestamps(lyrics_lines)

    # Find the closest timestamp
    closest_index = find_closest_timestamp(timestamps, input_timestamp)
    if closest_index is None:
        await ctx.reply(f"No matching timestamp found for **{track_name.title()}** 🤓☝️")
        return

    # Collect and send the lyrics around the closest timestamp
    current_lyrics = collect_lyrics(timestamps, closest_index)
    if source == 'last.fm':
        await ctx.send(f'**{track_name.title()}**\n\n{current_lyrics.strip()}\n\n *using last.fm as source for currently playing*')
    else:
        await ctx.send(f'**{track_name.title()}**\n\n{current_lyrics.strip()}')

def convert_timestamp_to_seconds(timestamp: str) -> int:
    """Convert a timestamp in hh:mm:ss format to total seconds."""
    try:
        h, m, s = map(int, timestamp.split(':'))
        return h * 3600 + m * 60 + s
    except ValueError:
        raise ValueError("Invalid timestamp format. Please use hh:mm:ss.")

def extract_timestamps(lyrics_lines: list) -> list:
    """Extract timestamps from lyrics lines."""
    timestamps = []
    for line in lyrics_lines:
        if '[' in line and ']' in line:
            ts_str = line[line.find('[') + 1:line.find(']')]
            ts_parts = ts_str.split('.')
            if len(ts_parts) == 2:
                ts_min_sec, ts_ms = ts_parts
                ts_min, ts_sec = map(int, ts_min_sec.split(':'))
                ts_total = ts_min * 60 + ts_sec
                timestamps.append((ts_total, line[line.find(']') + 1:].strip()))
    return timestamps

def find_closest_timestamp(timestamps: list, input_timestamp: int) -> int:
    """Find the closest timestamp to the input timestamp."""
    closest_index = None
    min_diff = float('inf')
    for idx, (ts, _) in enumerate(timestamps):
        diff = abs(ts - input_timestamp)
        if diff < min_diff:
            min_diff = diff
            closest_index = idx
    return closest_index

def collect_lyrics(timestamps: list, closest_index: int) -> str:
    """Collect the lyrics around the closest timestamp."""
    start = max(0, closest_index - 4)
    end = min(len(timestamps), closest_index + 3)
    return '\n'.join([timestamps[i][1] for i in range(start, end)])
