from discord.ext import commands


def disabled() -> commands.check:
    def predicate(_: commands.Context) -> bool:
        raise commands.DisabledCommand("This command is disabled.")

    return commands.check(predicate)
