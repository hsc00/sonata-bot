from __future__ import annotations

import re

from api.genius import get_track_relationships
from api.last_fm import get_last_played
from core.embeds import lyrics_embed, paginate_embeds, samples_embed
from core.errors import NoLastFMUsernameError, NoLyricsFoundError
from database import UserInfo
from discord import app_commands
from discord.ext import commands
from syncedlyrics import search


class TracksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="lyrics", aliases=["lr"], with_app_command=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lyrics(self, ctx: commands.Context) -> None:
        """Get the lyrics for a given track."""
        user_id = str(ctx.author.id)
        user = UserInfo.get_or_none(UserInfo.user_id == user_id)
        last_fm_username = user.lastfm_username if user else None

        if last_fm_username is None:
            raise NoLastFMUsernameError

        # TODO: This can be refactored to use "fetch_album" (which should be renamed)
        #       to get the last played track with album and artist data
        async with ctx.typing():
            _, artist_name, track_name = get_last_played(last_fm_username)
            synced_lyrics = search(f"{artist_name} - {track_name}")

            if not synced_lyrics or synced_lyrics == "":
                raise NoLyricsFoundError

            # Remove the timestamp from the lyrics
            lyrics_lines = [
                re.sub(r"^\[.+](.*)$", r"\1", line).strip()
                for line in synced_lyrics.split("\n")
            ]

            view, pages = paginate_embeds(
                lyrics_lines,
                lyrics_embed,
                per_page=20,
                title=track_name,
                artist=artist_name,
            )

        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(name="samples", with_app_command=True)
    async def samples(
        self,
        ctx: commands.Context,
        *,
        track_name: str | None = None,
    ) -> None:
        artist_name = None

        if track_name is None:
            user_id = str(ctx.author.id)
            user = UserInfo.get_or_none(UserInfo.user_id == user_id)
            last_fm_username = user.lastfm_username if user else None

            if last_fm_username is None:
                raise NoLastFMUsernameError

            _, artist_name, track_name = get_last_played(last_fm_username)

        async with ctx.typing():
            relationships_data = get_track_relationships(
                track_name if artist_name is None else f"{artist_name} - {track_name}",
            )

            if relationships_data is None or (
                len(relationships_data["relationships"]["samples"]) == 0
                and len(relationships_data["relationships"]["interpolates"]) == 0
                and len(relationships_data["relationships"]["sampled_in"]) == 0
            ):
                await ctx.send("💔 No samples found for this track.")

                return

            embed = samples_embed(
                relationships_data["artist_name"],
                relationships_data["track_name"],
                relationships_data["cover_url"],
                relationships_data["url"],
                [
                    relationships_data["relationships"]["samples"],
                    relationships_data["relationships"]["interpolates"],
                    relationships_data["relationships"]["sampled_in"],
                ],
            )

            await ctx.send(embed=embed)
