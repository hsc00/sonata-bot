from discord.ext import commands


def disabled():
    def predicate(_):
        raise commands.DisabledCommand("This command is disabled.")

    return commands.check(predicate)
