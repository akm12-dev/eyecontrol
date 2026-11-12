from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoteSession:
    """An established session with a remote agent (created by ``connect`` once implemented)."""

    device_id: str
    computer_name: str
