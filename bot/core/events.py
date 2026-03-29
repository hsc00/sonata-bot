import logging

from core.errors import SonataError
from discord.ext import commands
from discord.ext.commands import CommandNotFound

logger = logging.getLogger(__name__)


def init_events(bot: commands.Bot) -> None:
    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception) -> None:
        logger.error(error)

        if isinstance(error, CommandNotFound):
            pass

        else:
            original = getattr(error, "original", error)

            if isinstance(original, SonataError):
                await ctx.send(original.message)

            else:
                await ctx.send(
                    "❌ An unexpected error occurred. Please try again later."
                )
