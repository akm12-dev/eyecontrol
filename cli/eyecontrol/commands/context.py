from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console

from eyecontrol.auth import TechnicianSession
from eyecontrol.commands.registry import Registry
from eyecontrol.config import Settings
from eyecontrol.network import RemoteSession
from eyecontrol.remote import RustDeskClient, RustDeskServer


@dataclass
class AppContext:
    """Everything a command handler needs. One instance per process."""

    console: Console
    settings: Settings
    registry: Registry
    interactive: bool
    technician: TechnicianSession = field(default_factory=TechnicianSession)
    remote: RemoteSession | None = None
    log_file: str | None = None
    rustdesk_client: RustDeskClient | None = None

    @property
    def rustdesk(self) -> RustDeskClient:
        if self.rustdesk_client is None:
            server = RustDeskServer(self.settings.rustdesk_host, self.settings.rustdesk_key)
            self.rustdesk_client = RustDeskClient(server, executable=self.settings.rustdesk_client)
        return self.rustdesk_client

    @property
    def prompt_label(self) -> str:
        return self.remote.device_id if self.remote else "eyecontrol"
