from __future__ import annotations

import io
from pathlib import Path

import pytest

from eyecontrol.commands import build_registry
from eyecontrol.commands.context import AppContext
from eyecontrol.config import load_settings
from eyecontrol.ui.theme import make_console


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Never touch the real %APPDATA% / %LOCALAPPDATA% during tests."""
    monkeypatch.setenv("EYECONTROL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("EYECONTROL_DATA_DIR", str(tmp_path / "data"))
    for var in ("EYECONTROL_SERVER_URL", "EYECONTROL_ENV", "EYECONTROL_LOG_LEVEL"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


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
