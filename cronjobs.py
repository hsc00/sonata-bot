import asyncio
from discord.ext import commands
from datetime import datetime, timedelta
from commands.newreleases import get_new_releases
from commands.randomrating import get_random_rating_from_cache

async def new_releases_friday(channel, bot, BotMessage):
    while True:
        now = datetime.now()

        # Calculate the next Wednesday at 00:00
        next_wednesday = now + timedelta((2 - now.weekday()) % 7)
        next_wednesday_midnight = next_wednesday.replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate the next Friday at 00:00
        next_friday = now + timedelta((4 - now.weekday()) % 7)
        next_friday_midnight = next_friday.replace(hour=0, minute=0, second=0, microsecond=0)

        # Determine which event should come first
        if now.weekday() in [2, 4]:  # If today is Wednesday or Friday, run immediately
            time_until_next_event = 0
        elif now < next_wednesday_midnight:
            time_until_next_event = (next_wednesday_midnight - now).total_seconds()
        elif now < next_friday_midnight:
            time_until_next_event = (next_friday_midnight - now).total_seconds()
        else:
            # If already past Friday midnight, skip to the next week
            time_until_next_event = (next_wednesday_midnight + timedelta(days=7) - now).total_seconds()

        # Sleep until the next relevant event
        await asyncio.sleep(time_until_next_event)

        if now.weekday() == 2:  # Wednesday check
            author = bot.user
            bot_message = BotMessage(channel, author, '!newreleases')
            ctx = await bot.get_context(bot_message, cls=commands.Context)
            await get_new_releases(ctx)

        if now.weekday() == 4:  # Friday release announcements
            await channel.send("# This week's new releases are out 🎉🎉")
            bot_message = BotMessage(channel, bot.user, '!newreleases')
            ctx = await bot.get_context(bot_message, cls=commands.Context)
            await get_new_releases(ctx)

            # Wait until 12:00 PM Friday
            await asyncio.sleep(43200)
            await get_new_releases(ctx)

            # Wait until 12:00 AM Saturday
            await asyncio.sleep(43200)
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