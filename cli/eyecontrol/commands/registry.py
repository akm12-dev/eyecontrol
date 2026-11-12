"""Command model shared by the interactive console and direct ``eyecontrol <command>`` calls.

Both entry points go through :meth:`Registry.execute`, so validation, scope
checks, logging and error semantics are identical in the two modes.
"""

from __future__ import annotations

import difflib
import shlex
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import Flag, auto
from typing import TYPE_CHECKING

from eyecontrol.logging_setup import get_logger

if TYPE_CHECKING:
    from eyecontrol.commands.context import AppContext

log = get_logger("commands")


class CommandScope(Flag):
    INTERACTIVE = auto()  # typed at the ``eyecontrol >`` prompt
    DIRECT = auto()  # run as ``eyecontrol <command>`` from CMD / PowerShell / bash
    BOTH = INTERACTIVE | DIRECT


class ExitCode:
    OK = 0
    ERROR = 1
    USAGE = 2
    NOT_AVAILABLE = 3
    INTERRUPTED = 130


class CommandError(Exception):
    exit_code = ExitCode.ERROR

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class UsageError(CommandError):
    exit_code = ExitCode.USAGE


class NotAvailableError(CommandError):
    """The command exists in the design but is not implemented yet. Nothing was executed."""

    exit_code = ExitCode.NOT_AVAILABLE

    def __init__(self, command: str, phase: str) -> None:
        super().__init__(
            f"'{command}' is not available yet, planned for {phase}.",
            hint="Nothing was sent or executed. See 'help' for the commands that work today.",
        )
        self.command = command
        self.phase = phase


class ExitRequested(Exception):
    """Raised by ``exit`` to leave the interactive console."""


Handler = Callable[["AppContext", Sequence[str]], None]
Validator = Callable[[Sequence[str]], None]


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    summary: str
    handler: Handler
    usage: str = ""
    min_args: int = 0
    max_args: int | None = 0
    scope: CommandScope = CommandScope.BOTH
    aliases: tuple[str, ...] = ()
    category: str = "General"
    planned_phase: str | None = None  # None = implemented
    arg_choices: tuple[str, ...] | None = None  # allowed values for the first argument
    validator: Validator | None = None  # extra validation (options, formats)

    @property
    def available(self) -> bool:
        return self.planned_phase is None

    @property
    def usage_line(self) -> str:
        return f"{self.name} {self.usage}".strip()

    def check_args(self, args: Sequence[str]) -> None:
        too_few = len(args) < self.min_args
        too_many = self.max_args is not None and len(args) > self.max_args
        if too_few or too_many:
            raise UsageError(f"wrong number of arguments for '{self.name}'.", hint=f"Usage: {self.usage_line}")
        if self.arg_choices and args and args[0].lower() not in self.arg_choices:
            choices = ", ".join(self.arg_choices)
            raise UsageError(
                f"'{args[0]}' is not valid for '{self.name}' (expected: {choices}).", hint=f"Usage: {self.usage_line}"
            )
        if self.validator:
            try:
                self.validator(args)
            except UsageError as exc:
                raise UsageError(exc.message, hint=exc.hint or f"Usage: {self.usage_line}") from None


class Registry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._lookup: dict[str, Command] = {}

    def register(self, command: Command) -> Command:
        for key in (command.name, *command.aliases):
            if key in self._lookup:
                raise ValueError(f"command name {key!r} registered twice")
            self._lookup[key] = command
        self._commands[command.name] = command
        return command

    def commands(self, scope: CommandScope | None = None) -> list[Command]:
        return [c for c in self._commands.values() if scope is None or scope & c.scope]

    def names(self, scope: CommandScope | None = None, *, include_aliases: bool = False) -> list[str]:
        result: list[str] = []
        for command in self.commands(scope):
            result.append(command.name)
            if include_aliases:
                result.extend(command.aliases)
        return result

    def get(self, name: str) -> Command | None:
        return self._lookup.get(name.lower())

    def resolve(self, name: str, scope: CommandScope) -> Command:
        command = self.get(name)
        if command is None:
            close = difflib.get_close_matches(name.lower(), self.names(scope, include_aliases=True), n=1)
            hint = f"Did you mean '{close[0]}'?" if close else "Type 'help' for available commands."
            raise UsageError(f"unknown command '{name}'.", hint=hint)
        if not scope & command.scope:
            if scope is CommandScope.DIRECT:
                raise UsageError(
                    f"'{command.name}' can only be used inside the interactive console.",
                    hint="Run 'eyecontrol' first, then type the command at the prompt.",
                )
            raise UsageError(f"'{command.name}' can only be run directly from the command line (eyecontrol {command.name}).")
        return command

    def execute(self, ctx: AppContext, name: str, args: Sequence[str], scope: CommandScope) -> None:
        command = self.resolve(name, scope)
        command.check_args(args)
        # Never log argument values: later commands (login, ...) may receive secrets.
        log.info("command", extra={"fields": {"command": command.name, "argc": len(args), "mode": scope.name}})
        command.handler(ctx, args)


def parse_line(line: str) -> list[str]:
    """Split a console line into tokens. Quotes group words; backslashes stay literal (Windows paths)."""
    lexer = shlex.shlex(line, posix=True)
    lexer.whitespace_split = True
    lexer.escape = ""
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        raise UsageError("could not read the command.", hint="Check that quotes are closed.") from None


def iter_categories(commands: Iterable[Command]) -> dict[str, list[Command]]:
    grouped: dict[str, list[Command]] = {}
    for command in commands:
        grouped.setdefault(command.category, []).append(command)
    return grouped
