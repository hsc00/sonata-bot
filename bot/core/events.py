import logging

from discord.ext.commands import CommandNotFound

from core.errors import SonataError

logger = logging.getLogger(__name__)


def init_events(bot):
    @bot.event
    async def on_command_error(ctx, error: Exception):
        logger.error(error)

        try:
            original = getattr(error, "original", error)

            if isinstance(original, SonataError):
                await ctx.send(original.message)

            else:
                raise original

        except CommandNotFound:
            pass

        except Exception:
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
