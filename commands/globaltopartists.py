import requests
from bs4 import BeautifulSoup
import discord
from views import *

def setup(bot):
    @bot.command(name='globaltopartists')
    async def globaltopartists(ctx):
        async with ctx.channel.typing():
            await get_global_top_artists(ctx)

    @bot.command(name='gta')
    async def gta(ctx):
        async with ctx.channel.typing():
            await get_global_top_artists(ctx)

async def get_global_top_artists(ctx):

    url = 'https://kworb.net/itunes/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    artists = []
    position_changes = []

    # Check if the bot has the emojis
    emoji_increase = discord.utils.get(ctx.guild.emojis, name='increase')
    emoji_decrease = discord.utils.get(ctx.guild.emojis, name='decrease')
    emoji_equal = discord.utils.get(ctx.guild.emojis, name='equal')

    rows = soup.find_all('tr')[1:101]
    for row in rows:
        artist = row.find_all('td')[2].text.strip()
        position_change = row.find_all('td')[1].text.strip()

        if emoji_increase:
            position_change = position_change.replace('+', f'<:{emoji_increase.name}:{emoji_increase.id}>')
        if emoji_decrease:
            position_change = position_change.replace('-', f'<:{emoji_decrease.name}:{emoji_decrease.id}>')
        if emoji_equal:
            position_change = position_change.replace('=', f'<:{emoji_equal.name}:{emoji_equal.id}>')

        artists.append(artist)
        position_changes.append(position_change)

    top_artists = list(zip(artists, position_changes))

    if top_artists:
        embeds = []
        embed_title = "Top 100 Artists"
        for i in range(0, len(top_artists), 10):
            page = top_artists[i:i + 10]
            embed_description = "\n".join(
                f"{i + index + 1}. ({position_change}) [{artist}](https://rateyourmusic.com/artist/{artist.replace(' ', '-').lower()})"
                for index, (artist, position_change) in enumerate(page)
            )
            embed_color = discord.Color.blue()
            embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • Page {(i // 10) + 1}/{len(top_artists) // 10}")
            embeds.append(embed)
        sent_message = await ctx.channel.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
    else:
        await ctx.channel.send("No data found for the top artists.")
