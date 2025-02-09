global ratings_cache
ratings_cache = dict()
bot_instance = None

async def on_message(message):
    if message.author == bot_instance.user:
        return

    if 'rateyourmusic.com/release/' in message.content and len(message.content.split('/')) > 5:
        message.content = "!ab " + message.content
        await bot_instance.process_commands(message)
    elif 'rateyourmusic.com/artist/' in message.content and len(message.content.split('/')) > 3:
        message.content = "!a " + message.content
        await bot_instance.process_commands(message)

def setup(bot):
    global bot_instance
    bot_instance = bot
    bot.add_listener(on_message)
