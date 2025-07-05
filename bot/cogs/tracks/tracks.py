import re

from discord.ext import commands
from syncedlyrics import search

from api.last_fm import get_last_played
from core.utils import paginate_embeds
from database import UserInfo
from core.embeds import lyrics_embed


class TracksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["lr"])
    async def lyrics(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        last_fm_username = UserInfo.get_or_none(
            UserInfo.user_id == user_id,
        ).lastfm_username

        if last_fm_username is None:
            raise Exception(
                "❌ No last.fm username set. Please provide a search term or set your last.fm username by running `!set_lastfm <username>`."
            )

        # TODO: This can be refactored to use "fetch_album" (which should be renamed)
        #       to get the last played track with album and artist data
        async with ctx.typing():
            album_name, artist_name, track_name = get_last_played(last_fm_username)
            synced_lyrics = search(f"{artist_name} - {track_name}")

            if not synced_lyrics or synced_lyrics == "":
                await ctx.send(content=f"❌ No lyrics found.")

            # Remove the timestamp from the lyrics
            lyrics_lines = [re.sub(r"^\[.+](.*)$", r"\1", line).strip() for line in synced_lyrics.split('\n')]

            view, pages = paginate_embeds(
                lyrics_lines,
                lyrics_embed,
                per_page=20,
                title=track_name,
                artist=artist_name,
            )

        await ctx.send(embed=pages[0], view=view)
