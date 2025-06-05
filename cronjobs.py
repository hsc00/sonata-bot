import asyncio
from discord.ext import commands
from datetime import datetime
from commands.newreleases import get_new_releases
from commands.randomrating import get_random_rating_from_cache

async def new_releases_cronjob(channel, bot, BotMessage):
    while True:
        try:
            # Log the check time
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Checking for new releases at {now}")

            bot_message = BotMessage(channel, bot.user, '!newreleases')
            ctx = await bot.get_context(bot_message, cls=commands.Context)
            await get_new_releases(ctx)

            # Wait 12 hours before checking again
            await asyncio.sleep(43200)

        except Exception as e:
            print(f"Error in new releases cronjob: {e}")


async def random_rating_cronjob(channel, bot, BotMessage):
    while True:
        try:
            await asyncio.sleep(14400)  # 4 hours delay
            author = bot.user
            bot_message = BotMessage(channel, author, '!randomrating')

            ctx = await bot.get_context(bot_message, cls=commands.Context)
            async with ctx.channel.typing():
                await get_random_rating_from_cache(ctx, None, None)
                
        except Exception as e:
            print(f"Error in random rating cronjob: {e}")