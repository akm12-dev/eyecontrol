from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console

from eyecontrol.auth import TechnicianSession
from eyecontrol.commands.registry import Registry
from eyecontrol.config import Settings
from eyecontrol.network import RemoteSession


@dataclass(slots=True)
class AppContext:
    """Everything a command handler needs. One instance per process."""

    console: Console
    settings: Settings
    registry: Registry
    interactive: bool
    technician: TechnicianSession = field(default_factory=TechnicianSession)
    remote: RemoteSession | None = None
    log_file: str | None = None

    @property
    def prompt_label(self) -> str:
        return self.remote.device_id if self.remote else "eyecontrol"
