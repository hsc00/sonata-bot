import re

from discord.ext import commands
from syncedlyrics import search

from api.last_fm import get_last_played
from core.decorators import disabled
from core.errors import NoLyricsFound, NoLastFMUsername
from database import UserInfo
from core.embeds import lyrics_embed, paginate_embeds


class TracksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lyrics", aliases=["lr"])
    async def lyrics(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        user = UserInfo.get_or_none(UserInfo.user_id == user_id)
        last_fm_username = user.lastfm_username if user else None

        if last_fm_username is None:
            raise NoLastFMUsername()

        # TODO: This can be refactored to use "fetch_album" (which should be renamed)
        #       to get the last played track with album and artist data
        async with ctx.typing():
            album_name, artist_name, track_name = get_last_played(last_fm_username)
            synced_lyrics = search(f"{artist_name} - {track_name}")

            if not synced_lyrics or synced_lyrics == "":
                raise NoLyricsFound()

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

    @disabled()
    @commands.command()
    async def samples(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        user = UserInfo.get_or_none(UserInfo.user_id == user_id)
        last_fm_username = user.lastfm_username if user else None
