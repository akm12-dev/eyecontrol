"""Server link and remote-session state.

Phase 2: no network code runs. Phase 3 adds the HTTPS API client (HTTPX),
phase 4+ the secure WebSocket signalling channel to agents.
"""

from eyecontrol.network.session import RemoteSession

__all__ = ["RemoteSession"]
