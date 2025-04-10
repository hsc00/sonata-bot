import asyncio
from discord.ext import commands
from datetime import datetime, timedelta
from commands.newreleases import get_new_releases
from commands.randomrating import get_random_rating_from_cache

async def new_releases_friday(channel, bot, BotMessage):
    while True:
        # Get the current time
        now = datetime.now()

        # Calculate the next Friday at 00:00
        # Start by getting today's date and the time for 00:00
        next_friday = now + timedelta((4 - now.weekday()) % 7)  # 4 = Friday (Monday is 0)
        next_friday_midnight = next_friday.replace(hour=0, minute=0, second=0, microsecond=0)

        # If it's already past 00:00 on Friday, we need to skip to the following Friday
        if now >= next_friday_midnight:
            next_friday_midnight += timedelta(days=7)

        # Calculate the remaining time until the next Friday at 00:00
        time_until_next_friday = (next_friday_midnight - now).total_seconds()
        
        # Sleep until the next Friday at 00:00
        await asyncio.sleep(time_until_next_friday)

        # Execute your task
        async with channel.typing():
            await channel.send("This week's new releases are out!")
            author = bot.user
            bot_message = BotMessage(channel, author, '!newreleases')

            ctx = await bot.get_context(bot_message, cls=commands.Context)
            async with ctx.channel.typing():
                await get_new_releases(ctx)


async def random_rating_cronjob(channel, bot, BotMessage):
    await asyncio.sleep(21600) # Sends a random rating every 6 hours
    author = bot.user
    bot_message = BotMessage(channel, author, '!randomrating')

    ctx = await bot.get_context(bot_message, cls=commands.Context)
    async with ctx.channel.typing():
        await get_random_rating_from_cache(ctx, None, None)