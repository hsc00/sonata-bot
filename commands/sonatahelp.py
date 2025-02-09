import discord
from views import Paginator

def setup(bot):
    @bot.command(name='sonatahelp')
    async def sonatahelp(ctx):
        # Read the content of help.txt
        with open('help.txt', 'r') as file:
            help_content = file.readlines()

        # Replace the placeholder with the actual hyperlink
        help_content = [line.replace("[here]", "[here](https://discord.com/channels/1033860114026860645/1034393375291482112/1335231831284383825)") for line in help_content]

        # Split the help content into pages of 10 lines each
        pages = [''.join(help_content[i:i + 10]) for i in range(0, len(help_content), 10)]
        embeds = []

        for i, page in enumerate(pages):
            embed = discord.Embed(
                title="Welcome to Sonata Bot!",
                description=page,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • Page {i + 1}/{len(pages)}")
            embeds.append(embed)

        sent_message = await ctx.send(embed=embeds[0])
        view = Paginator(embeds)
        await sent_message.edit(embed=embeds[0], view=view)
