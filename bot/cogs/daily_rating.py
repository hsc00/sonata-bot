from __future__ import annotations

import logging

import discord
from core.embeds import rating_embed
from database import GuildConfig, Rating
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class DailyRatingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.loop.create_task(self._daily_random_rating_loop())

    async def _daily_random_rating_loop(self) -> None:
        await self.bot.wait_until_ready()
        logger.info("Daily random rating loop started.")

        while not self.bot.is_closed():
            try:
                await self._post_daily_random_rating()
            except Exception:
                logger.exception("Failed to post daily random rating.")

            now = discord.utils.utcnow()
            configs = list(
                GuildConfig.select().where(GuildConfig.daily_random_rating_enabled == 1)
            )
            hours = [
                config.daily_random_rating_hour
                for config in configs
                if config.daily_random_rating_hour is not None
            ]
            target_hour = max(set(hours), key=hours.count) if hours else 12
            next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += __import__("datetime").timedelta(days=1)

            await discord.utils.sleep_until(next_run)

    async def _post_daily_random_rating(self) -> None:
        configs = GuildConfig.select().where(
            GuildConfig.daily_random_rating_enabled == 1
        )

        for config in configs:
            if not config.channel_id:
                continue

            channel = self.bot.get_channel(int(config.channel_id))
            if channel is None:
                continue

            rating = (
                Rating.select().order_by(__import__("random").random()).limit(1).first()
            )

            if rating is None:
                continue

            embed = rating_embed(rating.user, rating)
            await channel.send(embed=embed)

    @app_commands.command(
        name="dailyrandomrating",
        description="Configure or disable the daily random rating feature for this guild",
    )
    @app_commands.allowed_contexts(guilds=True)
    @app_commands.describe(
        channel="Channel to post daily random ratings to",
        disable="Disable daily random ratings for this guild",
        hour="Hour of the day (UTC, 0-23) to post the random rating",
    )
    async def daily_random_rating(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        *,
        disable: bool = False,
        hour: int | None = None,
    ) -> None:
        """Configure or disable the daily random rating feature for this guild."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage

        if hour is not None and (hour < 0 or hour > 23):
            await ctx.send("Hour must be between 0 and 23.")
            return

        target_channel = channel or ctx.channel

        config, _ = GuildConfig.get_or_create(
            guild_id=str(ctx.guild.id),
            defaults={"channel_id": str(target_channel.id)},
        )

        if disable:
            if not config.daily_random_rating_enabled:
                await ctx.send("Daily random rating is not enabled for this guild.")
                return

            config.daily_random_rating_enabled = 0
            config.save()
            await ctx.send("Daily random rating disabled for this guild.")
            return

        if hour is not None:
            config.daily_random_rating_hour = hour

        config.channel_id = str(target_channel.id)
        config.daily_random_rating_enabled = 1
        config.save()

        post_hour = config.daily_random_rating_hour
        await ctx.send(
            f"Daily random rating enabled. Ratings will be posted to {target_channel.mention} every day at {post_hour:02d}:00 UTC."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DailyRatingCog(bot))
