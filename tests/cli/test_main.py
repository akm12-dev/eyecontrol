"""Direct mode (``eyecontrol <command>``) through Typer's test runner."""

from __future__ import annotations

from typer.testing import CliRunner

from eyecontrol import __version__
from eyecontrol.commands import ExitCode
from eyecontrol.main import app

runner = CliRunner()


def test_version_flag() -> None:
    for flag in ("--version", "-V"):
        result = runner.invoke(app, [flag])
        assert result.exit_code == 0
        assert result.output.strip() == f"EyeControl {__version__}"


def test_help_flag_lists_direct_commands_only() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("status", "login", "logout", "devices"):
        assert name in result.output
    assert "desktop" not in result.output  # console-only commands are hidden here


def test_status() -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == ExitCode.OK
    assert "not signed in" in result.output


def test_help_command() -> None:
    result = runner.invoke(app, ["help"])
    assert result.exit_code == ExitCode.OK
    assert "eyecontrol devices" in result.output


def test_planned_command_exit_code() -> None:
    result = runner.invoke(app, ["devices"])
    assert result.exit_code == ExitCode.NOT_AVAILABLE
    assert "not available yet" in result.output


def test_console_only_command_explains_where_to_run_it() -> None:
    result = runner.invoke(app, ["connect", "PC-001"])
    assert result.exit_code == ExitCode.USAGE
    assert "interactive console" in result.output


def test_unknown_command() -> None:
    result = runner.invoke(app, ["nope"])
    assert result.exit_code == 2


def test_no_arguments_opens_the_console_and_reads_stdin() -> None:
    result = runner.invoke(app, [], input="status\nexit\n")
    assert result.exit_code == ExitCode.OK
    assert "E Y E C O N T R O L" in result.output
    assert "eyecontrol > status" in result.output


def test_devices_type_option_from_terminal() -> None:
    assert runner.invoke(app, ["devices", "--type", "android"]).exit_code == ExitCode.NOT_AVAILABLE
    bad = runner.invoke(app, ["devices", "--type", "macos"])
    assert bad.exit_code == ExitCode.USAGE
    assert "unknown device type" in bad.output
