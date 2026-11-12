"""Technician authentication state.

Login is not implemented, so the technician is always signed out. Tokens,
if added later, belong in the OS keyring, never in plain files.
"""

from eyecontrol.auth.session import AuthState, TechnicianSession

__all__ = ["AuthState", "TechnicianSession"]
