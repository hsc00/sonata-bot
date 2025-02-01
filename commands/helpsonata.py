import discord

def setup(bot):
    @bot.command(name='helpsonata')
    async def helpsonata(ctx):
        # Read the content of help.txt
        with open('help.txt', 'r') as file:
            help_content = file.read()

        # Create an embed to display the help content
        embed = discord.Embed(
            title="Help",
            description=help_content,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
