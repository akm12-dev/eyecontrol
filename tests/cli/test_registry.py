from __future__ import annotations

import pytest

from eyecontrol.commands import (
    CommandScope,
    ExitCode,
    NotAvailableError,
    UsageError,
    build_registry,
    parse_line,
)
from eyecontrol.commands.context import AppContext


@pytest.mark.parametrize(
    ("line", "tokens"),
    [
        ("", []),
        ("   ", []),
        ("help", ["help"]),
        ("  shell   powershell ", ["shell", "powershell"]),
        ('connect "PC 001"', ["connect", "PC 001"]),
        (r"sysinfo C:\Users\Client", ["sysinfo", r"C:\Users\Client"]),  # backslashes kept for Windows paths
        ("help # not a comment", ["help", "#", "not", "a", "comment"]),
    ],
)
def test_parse_line(line: str, tokens: list[str]) -> None:
    assert parse_line(line) == tokens


def test_parse_line_unclosed_quote() -> None:
    with pytest.raises(UsageError):
        parse_line('connect "PC-001')


def test_all_specified_commands_exist() -> None:
    registry = build_registry()
    expected = {
        "login",
        "logout",
        "status",
        "devices",
        "connect",
        "disconnect",
        "shell",
        "desktop",
        "sysinfo",
        "help",
        "exit",
        "screen",
        "control",
    }
    assert expected <= set(registry.names())


def test_only_implemented_commands_are_marked_available() -> None:
    available = {c.name for c in build_registry().commands() if c.available}
    assert available == {"help", "status", "version", "clear", "exit"}


def test_scopes_separate_console_and_direct_commands() -> None:
    registry = build_registry()
    direct = set(registry.names(CommandScope.DIRECT))
    assert {"status", "login", "logout", "devices", "help", "version"} == direct
    interactive = set(registry.names(CommandScope.INTERACTIVE))
    assert {"connect", "shell", "desktop", "exit", "status"} <= interactive


def test_unknown_command_suggests_close_match(ctx: AppContext) -> None:
    with pytest.raises(UsageError) as info:
        ctx.registry.execute(ctx, "stauts", [], CommandScope.INTERACTIVE)
    assert info.value.hint == "Did you mean 'status'?"
    assert info.value.exit_code == ExitCode.USAGE


def test_console_only_command_refused_in_direct_mode(ctx: AppContext) -> None:
    with pytest.raises(UsageError, match="interactive console"):
        ctx.registry.execute(ctx, "connect", ["PC-001"], CommandScope.DIRECT)


def test_argument_count_is_checked(ctx: AppContext) -> None:
    with pytest.raises(UsageError, match="wrong number"):
        ctx.registry.execute(ctx, "connect", [], CommandScope.INTERACTIVE)
    with pytest.raises(UsageError, match="wrong number"):
        ctx.registry.execute(ctx, "status", ["extra"], CommandScope.INTERACTIVE)


def test_argument_choices_are_checked_before_availability(ctx: AppContext) -> None:
    with pytest.raises(UsageError, match="expected: cmd, powershell"):
        ctx.registry.execute(ctx, "shell", ["bash"], CommandScope.INTERACTIVE)
    with pytest.raises(NotAvailableError) as info:
        ctx.registry.execute(ctx, "shell", ["PowerShell"], CommandScope.INTERACTIVE)
    assert info.value.exit_code == ExitCode.NOT_AVAILABLE
    assert info.value.message == "'shell' is not available yet."


@pytest.mark.parametrize("name", ["login", "logout", "devices", "disconnect", "sysinfo", "desktop", "screen", "control"])
def test_planned_commands_never_pretend_to_work(ctx: AppContext, name: str) -> None:
    with pytest.raises(NotAvailableError):
        ctx.registry.execute(ctx, name, [], CommandScope.INTERACTIVE)


def test_aliases_resolve(ctx: AppContext) -> None:
    assert ctx.registry.resolve("quit", CommandScope.INTERACTIVE).name == "exit"
    assert ctx.registry.resolve("CLS", CommandScope.INTERACTIVE).name == "clear"


def test_duplicate_registration_is_rejected() -> None:
    registry = build_registry()
    with pytest.raises(ValueError):
        registry.register(registry.resolve("help", CommandScope.INTERACTIVE))


@pytest.mark.parametrize("args", [[], ["--type", "windows"], ["--type", "Android"], ["--type", "ios"], ["--type", "linux"]])
def test_devices_type_filter_is_validated_then_reported_unavailable(ctx: AppContext, args: list[str]) -> None:
    with pytest.raises(NotAvailableError):
        ctx.registry.execute(ctx, "devices", args, CommandScope.INTERACTIVE)


@pytest.mark.parametrize("args", [["--type"], ["--type", "macos"], ["--kind", "ios"], ["android"]])
def test_devices_bad_filters(ctx: AppContext, args: list[str]) -> None:
    with pytest.raises(UsageError):
        ctx.registry.execute(ctx, "devices", args, CommandScope.INTERACTIVE)


def test_no_shell_promise_for_mobiles() -> None:
    shell = build_registry().resolve("shell", CommandScope.INTERACTIVE)
    assert shell.arg_choices == ("cmd", "powershell")
    assert "computers" in shell.summary
