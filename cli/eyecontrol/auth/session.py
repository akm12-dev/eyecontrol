from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AuthState(StrEnum):
    SIGNED_OUT = "signed_out"
    SIGNED_IN = "signed_in"


@dataclass(slots=True)
class TechnicianSession:
    state: AuthState = AuthState.SIGNED_OUT
    username: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.state is AuthState.SIGNED_IN and self.username is not None
