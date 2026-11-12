from __future__ import annotations

import io
from collections.abc import Sequence
from pathlib import Path

import pytest

from eyecontrol.commands import build_registry
from eyecontrol.commands.context import AppContext
from eyecontrol.config import load_settings
from eyecontrol.remote import rustdesk as rustdesk_module
from eyecontrol.ui.theme import make_console


class LaunchRecorder:
    """Replaces process creation: records the RustDesk command lines instead of running them."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, args: Sequence[str]) -> None:
        self.calls.append(list(args))


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Never touch the real profile, never start RustDesk, never reach the network."""
    monkeypatch.setenv("EYECONTROL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("EYECONTROL_DATA_DIR", str(tmp_path / "data"))
    for var in ("APPDATA", "LOCALAPPDATA", "ProgramFiles", "ProgramW6432", "XDG_CONFIG_HOME"):
        monkeypatch.setenv(var, str(tmp_path / "sys" / var))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for var in (
        "EYECONTROL_SERVER_URL",
        "EYECONTROL_ENV",
        "EYECONTROL_LOG_LEVEL",
        "EYECONTROL_RUSTDESK_HOST",
        "EYECONTROL_RUSTDESK_KEY",
        "EYECONTROL_RUSTDESK_CLIENT",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(rustdesk_module.shutil, "which", lambda name: None)
    monkeypatch.setattr(rustdesk_module, "server_reachable", lambda host, port=21116, timeout=3.0: True)
    return tmp_path


@pytest.fixture(autouse=True)
def launches(monkeypatch: pytest.MonkeyPatch) -> LaunchRecorder:
    recorder = LaunchRecorder()
    monkeypatch.setattr(rustdesk_module, "_spawn_detached", recorder)
    return recorder


@pytest.fixture
def rustdesk_exe(tmp_path: Path) -> Path:
    """A fake installed RustDesk (C:\\Program Files\\RustDesk\\rustdesk.exe in the isolated profile)."""
    exe = tmp_path / "sys" / "ProgramFiles" / "RustDesk" / "rustdesk.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"MZ fake")
    return exe


@pytest.fixture
def output() -> io.StringIO:
    return io.StringIO()


@pytest.fixture
def ctx(output: io.StringIO) -> AppContext:
    return AppContext(
        console=make_console(file=output, width=120, force_terminal=False),
        settings=load_settings(),
        registry=build_registry(),
        interactive=True,
    )
