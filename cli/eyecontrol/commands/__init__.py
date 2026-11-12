"""Command registry shared by the interactive console and direct CLI calls."""

from eyecontrol.commands.registry import (
    Command,
    CommandError,
    CommandScope,
    ExitCode,
    ExitRequested,
    NotAvailableError,
    Registry,
    UsageError,
    parse_line,
)


def build_registry() -> Registry:
    from eyecontrol.commands.builtin import register_builtin
    from eyecontrol.commands.planned import register_planned
    from eyecontrol.commands.remote import register_remote

    registry = Registry()
    register_builtin(registry)
    register_remote(registry)
    register_planned(registry)
    return registry


__all__ = [
    "Command",
    "CommandError",
    "CommandScope",
    "ExitCode",
    "ExitRequested",
    "NotAvailableError",
    "Registry",
    "UsageError",
    "build_registry",
    "parse_line",
]
