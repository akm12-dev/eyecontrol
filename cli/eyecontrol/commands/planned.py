"""Commands that are part of the design but not implemented.

They are registered so that help, completion and argument validation are
final, but their handler only reports that they are not available yet.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eyecontrol.commands.context import AppContext
from eyecontrol.commands.registry import Command, CommandScope, Handler, NotAvailableError, Registry


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
    _planned(registry, "screen", "Show a smartphone screen (mobiles)", **session)
    _planned(registry, "control", "Enable authorized touch control (Android only)", **session)
