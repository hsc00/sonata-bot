from discord.ext.commands import CommandNotFound

from core.errors import SonataError


def init_events(bot):
    @bot.event
    async def on_command_error(ctx, error: Exception):
        try:
            original = getattr(error, "original", error)

            if isinstance(original, SonataError):
                await ctx.send(original.message)

            else:
                raise original

        except CommandNotFound as e:
            await ctx.send(f"❌ {e}. Please check the command name and try again.")

        except Exception as e:
            print(f"An error occurred while handling an error: {e.__class__.__name__}: {e}")

            await ctx.send("❌ An unexpected error occurred. Please try again later.")
