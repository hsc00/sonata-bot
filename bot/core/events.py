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

        except Exception as e:
            print(f"An error occurred while handling an error: {e}")

            await ctx.send("❌ An unexpected error occurred. Please try again later.")
