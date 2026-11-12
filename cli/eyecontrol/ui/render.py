"""Rich renderers for banner, help, status and errors."""

from __future__ import annotations

import platform
import sys
from collections.abc import Iterable
from typing import TYPE_CHECKING

from rich.console import Console, Group
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from eyecontrol import APP_NAME, __version__
from eyecontrol.commands.registry import Command, CommandError, CommandScope, NotAvailableError, iter_categories
from eyecontrol.ui.theme import supports_unicode, terminal_name

if TYPE_CHECKING:
    from eyecontrol.commands.context import AppContext

LOGO = """\
███████╗██╗   ██╗███████╗
██╔════╝╚██╗ ██╔╝██╔════╝
█████╗   ╚████╔╝ █████╗
██╔══╝    ╚██╔╝  ██╔══╝
███████╗   ██║   ███████╗
╚══════╝   ╚═╝   ╚══════╝"""

LOGO_ASCII = """\
 _____ __   __ _____
| ____|\\ \\ / /| ____|
|  _|   \\ V / |  _|
| |___   | |  | |___
|_____|  |_|  |_____|"""

WHERE = {
    CommandScope.INTERACTIVE: "interactive console",
    CommandScope.DIRECT: "command line (eyecontrol <command>)",
    CommandScope.BOTH: "interactive console and command line",
}


def _state_lines(ctx: AppContext) -> list[tuple[str, Text]]:
    settings = ctx.settings
    if settings.server_url:
        server = Text.assemble((settings.server_url, "label"), ("  (not connected)", "muted"))
    else:
        server = Text("not configured", style="warn")
    if ctx.technician.is_authenticated:
        tech = Text(f"signed in as {ctx.technician.username}", style="ok")
    else:
        tech = Text("not signed in", style="warn")
    if ctx.remote:
        remote = Text(f"{ctx.remote.device_id} ({ctx.remote.computer_name})", style="ok")
    else:
        remote = Text("none", style="muted")
    return [("Server", server), ("Technician", tech), ("Session", remote)]


def banner(ctx: AppContext) -> None:
    console = ctx.console
    unicode_ok = supports_unicode(console)
    logo = Text(LOGO if unicode_ok else LOGO_ASCII, style="logo")
    title = Text("E Y E C O N T R O L", style="accent")
    subtitle = Text.assemble(("Remote Access Terminal", "label"), ("   |   ", "muted"), (f"Version {__version__}", "muted"))

    states = Table.grid(padding=(0, 2))
    states.add_column(style="label", no_wrap=True)
    states.add_column()
    for label, value in _state_lines(ctx):
        states.add_row(label, value)

    dot = "●" if unicode_ok else "*"
    hint = Text.assemble(
        (f"{dot} ", "muted"),
        ("Type ", "muted"),
        ("help", "cmd"),
        (" for available commands, ", "muted"),
        ("exit", "cmd"),
        (" or Ctrl+D to quit.", "muted"),
    )
    body = Group(
        logo, Text(), title, subtitle, Text(), Text(f"Welcome to {APP_NAME}.", style="bold"), Text(), states, Text(), hint
    )
    console.print()
    console.print(Padding(body, (0, 2)))
    for warning in ctx.settings.warnings:
        console.print(Padding(Text(f"! {warning}", style="warn"), (0, 2)))
    console.print()


def help_table(console: Console, commands: Iterable[Command], *, interactive: bool) -> None:
    table = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    table.add_column(no_wrap=True)
    table.add_column()
    table.add_column(no_wrap=True)
    for category, cmds in iter_categories(commands).items():
        table.add_row(Text(category.upper(), style="muted"), "", "")
        for command in cmds:
            name = command.usage_line if interactive else f"eyecontrol {command.usage_line}"
            state = Text("ready", style="ok") if command.available else Text("planned", style="planned")
            table.add_row(Text(f"  {name}", style="cmd" if command.available else "planned"), command.summary, state)
        table.add_row("", "", "")
    console.print(Padding(table, (1, 2, 0, 2)))
    footer = (
        "Type 'help <command>' for details."
        if interactive
        else "Run 'eyecontrol' without arguments to open the interactive console."
    )
    console.print(Padding(Text(footer, style="muted"), (0, 2, 1, 2)))


def command_help(console: Console, command: Command) -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="label", no_wrap=True)
    grid.add_column()
    grid.add_row("Usage", Text(command.usage_line, style="cmd"))
    grid.add_row("Description", command.summary)
    if command.aliases:
        grid.add_row("Aliases", ", ".join(command.aliases))
    grid.add_row("Where", WHERE.get(command.scope, WHERE[CommandScope.BOTH]))
    state = Text("ready", style="ok") if command.available else Text("not available yet", style="warn")
    grid.add_row("State", state)
    console.print(Padding(grid, (1, 2)))


def status(ctx: AppContext) -> None:
    settings = ctx.settings
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="label", no_wrap=True)
    grid.add_column()
    grid.add_row("Version", f"{APP_NAME} {__version__}")
    grid.add_row("Environment", settings.environment.value)
    for label, value in _state_lines(ctx):
        grid.add_row(label, value)
    config_state = "found" if settings.config_file.is_file() else "not created, optional"
    grid.add_row("Config file", Text.assemble(str(settings.config_file), (f"  ({config_state})", "muted")))
    grid.add_row("Log file", ctx.log_file or Text("disabled (log folder not writable)", style="warn"))
    grid.add_row("Terminal", terminal_name())
    grid.add_row("Platform", f"{platform.system()} {platform.release()}, Python {sys.version.split()[0]}")
    ctx.console.print(Padding(grid, (1, 2)))
    for warning in settings.warnings:
        ctx.console.print(Padding(Text(f"! {warning}", style="warn"), (0, 2)))


def error(console: Console, exc: CommandError) -> None:
    not_available = isinstance(exc, NotAvailableError)
    style = "warn" if not_available else "err"
    label = "Not available" if not_available else "Error"
    console.print(Text.assemble(("  ", ""), (f"{label}: ", style), exc.message))
    if exc.hint:
        console.print(Text(f"  {exc.hint}", style="muted"))
