import config
from views import *
from API.setlist_search import *

def setup(bot):
    @bot.command(name='setlists')
    async def setlists_command(ctx):
        async with ctx.message.channel.typing():
            await process_setlists(ctx.message)
            time.sleep(5)

    @bot.command(name='sts')
    async def sts_command(ctx):
        async with ctx.message.channel.typing():
            await process_setlists(ctx.message)
            time.sleep(5)

async def process_setlists(message):
    content_parts = message.content.split(' ', 1)
    if len(content_parts) > 1:
        query = content_parts[1]
        setlists = get_setlists(query, config.setlist_api_key)
        if not setlists or 'error' in setlists:
            await message.channel.send('Artist not found or timeout. Try again.')
            return
    else:
        await message.channel.send('Please provide a valid artist.')
        return
    
    pages = []
    for i in range(0, len(setlists), 5):
        embed_description = ""
        for setlist in setlists[i:i + 5]:
            artist_name = setlist['artist_name']
            artist_url = setlist['artist_url']
            date = setlist['concert_date']
            concert_name = setlist['concert_name']
            city_name = setlist['city_name']
            country_name = setlist['country_name']
            link = setlist['url']
            embed_description += f"{date}\n[{concert_name}, {city_name}, {country_name}]({link})\n\n"
        
        embed_title = f"{artist_name} (Last 10 Setlists)\n"
        embed = discord.Embed(title=embed_title, description=embed_description, url=artist_url)
        embed.set_footer(text=f"Requested by {message.author.display_name} • Page {i // 5 + 1}/{(len(setlists) + 4) // 5}")
        pages.append(embed)
    
    sent_message = await message.channel.send(embed=pages[0])
    view = Paginator(pages)
    await sent_message.edit(embed=pages[0], view=view)