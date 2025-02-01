import discord

def setup(bot):
    @bot.command(name='sonatahelp')
    async def sonatahelp(ctx):
        # Read the content of help.txt
        with open('help.txt', 'r') as file:
            help_content = file.read()

        # Replace the placeholder with the actual hyperlink
        help_content = help_content.replace("[here]", "[here](https://discord.com/channels/1033860114026860645/1034393375291482112/1335231831284383825)")

        # Create an embed to display the help content
        embed = discord.Embed(
            title="Welcome to Sonata Bot!",
            description=help_content,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
