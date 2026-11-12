"""End-to-end checks of the installed ``eyecontrol`` executable from CMD and PowerShell.

Skipped when the command is not on PATH (run inside the venv, or after installation).
These are non-interactive: the interactive prompt in a real console window is
checked manually (see docs/testing.md).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pytest

from eyecontrol import __version__
from eyecontrol.encoding import console_output_encoding

EXE = shutil.which("eyecontrol")
pytestmark = [
    pytest.mark.skipif(sys.platform != "win32", reason="Windows only"),
    pytest.mark.skipif(EXE is None, reason="eyecontrol is not on PATH"),
]


def run(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
        env=os.environ.copy(),
        encoding=console_output_encoding(),
        errors="replace",
    )


def test_cmd_version() -> None:
    result = run(["cmd.exe", "/d", "/c", "eyecontrol --version"])
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"EyeControl {__version__}"


def test_powershell_version_and_exit_code() -> None:
    script = "eyecontrol --version; eyecontrol devices *> $null; exit $LASTEXITCODE"
    result = run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script])
    assert f"EyeControl {__version__}" in result.stdout
    assert result.returncode == 3  # 'devices' is not available yet


def test_cmd_piped_session() -> None:
    result = run(["cmd.exe", "/d", "/c", "eyecontrol"], stdin="help\nstatus\nexit\n")
    assert result.returncode == 0, result.stderr
    assert "Remote Access Terminal" in result.stdout
    assert "Technician" in result.stdout
