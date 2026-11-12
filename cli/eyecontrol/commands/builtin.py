"""Commands implemented in version 0.1."""

from __future__ import annotations

from collections.abc import Sequence

from eyecontrol import APP_NAME, __version__
from eyecontrol.commands.context import AppContext
from eyecontrol.commands.registry import Command, CommandScope, ExitRequested, Registry, UsageError
from eyecontrol.ui import render


def _help(ctx: AppContext, args: Sequence[str]) -> None:
    scope = CommandScope.INTERACTIVE if ctx.interactive else CommandScope.DIRECT
    if args:
        command = ctx.registry.get(args[0])
        if command is None:
            raise UsageError(f"unknown command '{args[0]}'.", hint="Type 'help' for available commands.")
        render.command_help(ctx.console, command)
        return
    render.help_table(ctx.console, ctx.registry.commands(scope), interactive=ctx.interactive)


def _status(ctx: AppContext, args: Sequence[str]) -> None:
    render.status(ctx)


def _version(ctx: AppContext, args: Sequence[str]) -> None:
    ctx.console.print(f"{APP_NAME} {__version__}")


def _clear(ctx: AppContext, args: Sequence[str]) -> None:
    ctx.console.clear()


def _exit(ctx: AppContext, args: Sequence[str]) -> None:
    raise ExitRequested


def register_builtin(registry: Registry) -> None:
    registry.register(
        Command("help", "Show available commands, or details for one command", _help, usage="[command]", max_args=1)
    )
    registry.register(Command("status", "Show version, server, technician and session state", _status))
    registry.register(Command("version", "Show the EyeControl version", _version))
    registry.register(Command("clear", "Clear the screen", _clear, scope=CommandScope.INTERACTIVE, aliases=("cls",)))
    registry.register(Command("exit", "Leave EyeControl", _exit, scope=CommandScope.INTERACTIVE, aliases=("quit",)))
