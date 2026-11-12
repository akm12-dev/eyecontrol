"""Commands that are part of the design but not implemented.

They are registered so that help, completion and argument validation are
final, but their handler only reports that they are not available yet.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eyecontrol.commands.context import AppContext
from eyecontrol.commands.registry import Command, CommandScope, Handler, NotAvailableError, Registry, UsageError

DEVICE_TYPES = ("windows", "linux", "android", "ios")


def validate_devices_args(args: Sequence[str]) -> None:
    """Accepts nothing, or ``--type <windows|linux|android|ios>``."""
    if not args:
        return
    if len(args) != 2 or args[0] != "--type":
        raise UsageError("unknown option for 'devices'.")
    if args[1].lower() not in DEVICE_TYPES:
        raise UsageError(f"unknown device type '{args[1]}' (expected: {', '.join(DEVICE_TYPES)}).")


def _not_available(name: str) -> Handler:
    def handler(ctx: AppContext, args: Sequence[str]) -> None:
        raise NotAvailableError(name)

    return handler


def _planned(registry: Registry, name: str, summary: str, **kwargs: Any) -> None:
    registry.register(Command(name, summary, _not_available(name), planned=True, **kwargs))


def register_planned(registry: Registry) -> None:
    session = {"scope": CommandScope.INTERACTIVE, "category": "Session"}
    _planned(registry, "login", "Sign in as a technician", category="Account")
    _planned(registry, "logout", "Sign out and revoke the local token", category="Account")
    _planned(
        registry,
        "devices",
        "List the devices you are allowed to access (TYPE: windows, linux, android, ios)",
        category="Devices",
        usage="[--type TYPE]",
        max_args=2,
        validator=validate_devices_args,
    )
    _planned(registry, "connect", "Open a session with a remote device", usage="<device-id>", min_args=1, max_args=1, **session)
    _planned(registry, "disconnect", "Close the current remote session", **session)
    _planned(registry, "sysinfo", "Show system information of the connected device", **session)
    _planned(
        registry,
        "shell",
        "Open a remote CMD or PowerShell terminal (computers)",
        usage="cmd|powershell",
        min_args=1,
        max_args=1,
        arg_choices=("cmd", "powershell"),
        **session,
    )
    _planned(registry, "desktop", "View and control the remote desktop in a window (computers)", **session)
    _planned(registry, "screen", "Show the smartphone screen in the viewer (mobiles)", **session)
    _planned(registry, "control", "Enable authorized touch control (Android only)", **session)
