"""Technician authentication state.

Phase 2: there is no server yet, so the technician is always signed out.
Phase 3 will add login against the EyeControl server, MFA-ready token flow,
and token storage in the Windows Credential Manager (never in plain files).
"""

from eyecontrol.auth.session import AuthState, TechnicianSession

__all__ = ["AuthState", "TechnicianSession"]
