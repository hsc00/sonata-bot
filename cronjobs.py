import asyncio
from discord.ext import commands
from datetime import datetime, timedelta
from commands.newreleases import get_new_releases
from commands.randomrating import get_random_rating_from_cache

async def new_releases_friday(channel, bot, BotMessage):
    while True:
        # Get the current time
        now = datetime.now()

        # Calculate the next Wednesday at 00:00
        next_wednesday = now + timedelta((2 - now.weekday()) % 7)  # 2 = Wednesday (Monday is 0)
        next_wednesday_midnight = next_wednesday.replace(hour=0, minute=0, second=0, microsecond=0)

        # If it's already past 00:00 on Wednesday, skip to the following Wednesday
        if now >= next_wednesday_midnight:
            next_wednesday_midnight += timedelta(days=7)

        # Calculate the remaining time until the next Wednesday at 00:00
        time_until_next_wednesday = (next_wednesday_midnight - now).total_seconds()
        
        # Sleep until the next Wednesday at 00:00
        await asyncio.sleep(time_until_next_wednesday)

        # Mid-week check at 00:00 (Wednesday)
        author = bot.user
        bot_message = BotMessage(channel, author, '!newreleases')

        ctx = await bot.get_context(bot_message, cls=commands.Context)
        await get_new_releases(ctx)

        # Get the current time again for Friday calculations
        now = datetime.now()

        # Calculate the next Friday at 00:00
        next_friday = now + timedelta((4 - now.weekday()) % 7)  # 4 = Friday (Monday is 0)
        next_friday_midnight = next_friday.replace(hour=0, minute=0, second=0, microsecond=0)

        # If it's already past 00:00 on Friday, skip to the following Friday
        if now >= next_friday_midnight:
            next_friday_midnight += timedelta(days=7)

        # Calculate the remaining time until the next Friday at 00:00
        time_until_next_friday = (next_friday_midnight - now).total_seconds()
        
        # Sleep until the next Friday at 00:00
        await asyncio.sleep(time_until_next_friday)

        # First send at 00:00 (Friday)
        await channel.send("# This week's new releases are out 🎉🎉")
        bot_message = BotMessage(channel, bot.user, '!newreleases')
        ctx = await bot.get_context(bot_message, cls=commands.Context)
        await get_new_releases(ctx)

        # Wait until 12:00 (Friday)
        await asyncio.sleep(43200)  # 12 hours
        ctx = await bot.get_context(bot_message, cls=commands.Context)
        await get_new_releases(ctx)

        # Wait until 00:00 (transition to Saturday)
        await asyncio.sleep(43200)  # Another 12 hours
        ctx = await bot.get_context(bot_message, cls=commands.Context)
        await get_new_releases(ctx)


async def random_rating_cronjob(channel, bot, BotMessage):
    while True:
        try:
            await asyncio.sleep(21600)  # 6 hours (21600 seconds) delay
            author = bot.user
            bot_message = BotMessage(channel, author, '!randomrating')

            ctx = await bot.get_context(bot_message, cls=commands.Context)
            async with ctx.channel.typing():
                await get_random_rating_from_cache(ctx, None, None)
                
        except Exception as e:
            print(f"Error in random rating cronjob: {e}")