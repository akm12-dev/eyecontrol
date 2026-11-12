"""Commands that are part of the design but not implemented yet.

They are registered so that help, completion and argument validation are
already final, but their handler only reports that they are not available.
Each one is replaced by a real implementation in its phase (docs/roadmap.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eyecontrol.commands.context import AppContext
from eyecontrol.commands.registry import Command, CommandScope, Handler, NotAvailableError, Registry, UsageError

PHASE_SERVER = "phase 3 (server & authentication)"
PHASE_AGENT = "phase 4 (Windows agent & sessions)"
PHASE_SHELL = "phase 5 (remote terminal)"
PHASE_DESKTOP = "phase 6 (graphical control)"
PHASE_MOBILE = "Android milestone (mobile screen sharing)"
PHASE_ANDROID_CONTROL = "Android milestone (authorized touch control)"

DEVICE_TYPES = ("windows", "linux", "android", "ios")


def validate_devices_args(args: Sequence[str]) -> None:
    """Accepts nothing, or ``--type <windows|linux|android|ios>``."""
    if not args:
        return
    if len(args) != 2 or args[0] != "--type":
        raise UsageError("unknown option for 'devices'.")
    if args[1].lower() not in DEVICE_TYPES:
        raise UsageError(f"unknown device type '{args[1]}' (expected: {', '.join(DEVICE_TYPES)}).")


def _not_available(name: str, phase: str) -> Handler:
    def handler(ctx: AppContext, args: Sequence[str]) -> None:
        raise NotAvailableError(name, phase)

    return handler


def _planned(registry: Registry, name: str, summary: str, phase: str, **kwargs: Any) -> None:
    registry.register(Command(name, summary, _not_available(name, phase), planned_phase=phase, **kwargs))


def register_planned(registry: Registry) -> None:
    session = {"scope": CommandScope.INTERACTIVE, "category": "Session"}
    _planned(registry, "login", "Sign in as a technician", PHASE_SERVER, category="Account")
    _planned(registry, "logout", "Sign out and revoke the local token", PHASE_SERVER, category="Account")
    _planned(
        registry,
        "devices",
        "List the devices you are allowed to access",
        PHASE_SERVER,
        category="Devices",
        usage="[--type windows|linux|android|ios]",
        max_args=2,
        validator=validate_devices_args,
    )
    _planned(
        registry,
        "connect",
        "Open a session with a remote device",
        PHASE_AGENT,
        usage="<device-id>",
        min_args=1,
        max_args=1,
        **session,
    )
    _planned(registry, "disconnect", "Close the current remote session", PHASE_AGENT, **session)
    _planned(registry, "sysinfo", "Show system information of the connected device", PHASE_AGENT, **session)
    _planned(
        registry,
        "shell",
        "Open a remote CMD or PowerShell terminal (computers)",
        PHASE_SHELL,
        usage="cmd|powershell",
        min_args=1,
        max_args=1,
        arg_choices=("cmd", "powershell"),
        **session,
    )
    _planned(registry, "desktop", "View and control the remote desktop in a window (computers)", PHASE_DESKTOP, **session)
    _planned(registry, "screen", "Show the smartphone screen in the viewer (mobiles)", PHASE_MOBILE, **session)
    _planned(registry, "control", "Enable authorized touch control (Android only)", PHASE_ANDROID_CONTROL, **session)
