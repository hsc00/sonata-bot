from collections.abc import Callable

from discord.ext import commands

CommandDecorator = Callable[[commands.Command], commands.Command]


def disabled() -> CommandDecorator:
    def predicate(_: commands.Context) -> bool:
        raise commands.DisabledCommand("This command is disabled.")

    return commands.check(predicate)
