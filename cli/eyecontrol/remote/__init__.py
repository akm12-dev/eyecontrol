"""Remote sessions through RustDesk (self-hosted AKM12 server).

EyeControl does not capture screens or inject input itself: it drives the
RustDesk client installed on the technician's PC (``rustdesk --connect``,
``--terminal``, ``--file-transfer``). The person being helped runs the
RustDesk quick-support module and gives the ID and password, so every
session requires their participation. Passwords are typed in the RustDesk
window and never pass through EyeControl.
"""

from eyecontrol.remote.rustdesk import (
    ClientConfigState,
    KnownDevice,
    RustDeskClient,
    RustDeskError,
    RustDeskServer,
    normalize_id,
)

__all__ = [
    "ClientConfigState",
    "KnownDevice",
    "RustDeskClient",
    "RustDeskError",
    "RustDeskServer",
    "normalize_id",
]
