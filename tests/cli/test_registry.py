from __future__ import annotations

import pytest

from eyecontrol.commands import (
    CommandError,
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
        ("  shell   326245055 ", ["shell", "326245055"]),
        ('connect "326 245 055"', ["connect", "326 245 055"]),
        (r"sysinfo C:\Users\Client", ["sysinfo", r"C:\Users\Client"]),  # backslashes kept for Windows paths
        ("help # not a comment", ["help", "#", "not", "a", "comment"]),
    ],
)
def test_parse_line(line: str, tokens: list[str]) -> None:
    assert parse_line(line) == tokens


def test_parse_line_unclosed_quote() -> None:
    with pytest.raises(UsageError):
        parse_line('connect "PC-001')


def test_all_commands_exist() -> None:
    expected = {
        "login",
        "logout",
        "status",
        "devices",
        "connect",
        "disconnect",
        "shell",
        "desktop",
        "files",
        "sysinfo",
        "setup",
        "help",
        "exit",
        "screen",
        "control",
    }
    assert expected <= set(build_registry().names())


def test_available_and_planned_commands() -> None:
    commands = build_registry().commands()
    assert {c.name for c in commands if not c.available} == {"login", "logout", "screen", "control"}


def test_scopes_separate_console_and_direct_commands() -> None:
    registry = build_registry()
    direct = set(registry.names(CommandScope.DIRECT))
    assert direct == {"help", "status", "version", "login", "logout", "connect", "files", "devices", "setup"}
    interactive = set(registry.names(CommandScope.INTERACTIVE))
    assert {"connect", "shell", "desktop", "disconnect", "sysinfo", "exit", "status"} <= interactive


def test_unknown_command_suggests_close_match(ctx: AppContext) -> None:
    with pytest.raises(UsageError) as info:
        ctx.registry.execute(ctx, "stauts", [], CommandScope.INTERACTIVE)
    assert info.value.hint == "Did you mean 'status'?"
    assert info.value.exit_code == ExitCode.USAGE


def test_console_only_command_refused_in_direct_mode(ctx: AppContext) -> None:
    with pytest.raises(UsageError, match="interactive console"):
        ctx.registry.execute(ctx, "shell", ["326245055"], CommandScope.DIRECT)


def test_argument_count_is_checked(ctx: AppContext) -> None:
    with pytest.raises(UsageError, match="wrong number"):
        ctx.registry.execute(ctx, "connect", [], CommandScope.INTERACTIVE)
    with pytest.raises(UsageError, match="wrong number"):
        ctx.registry.execute(ctx, "status", ["extra"], CommandScope.INTERACTIVE)


@pytest.mark.parametrize("name", ["login", "logout", "screen", "control"])
def test_planned_commands_never_pretend_to_work(ctx: AppContext, name: str) -> None:
    with pytest.raises(NotAvailableError) as info:
        ctx.registry.execute(ctx, name, [], CommandScope.INTERACTIVE)
    assert info.value.exit_code == ExitCode.NOT_AVAILABLE


@pytest.mark.parametrize("args", [["--type"], ["--type", "solaris"], ["--kind", "ios"], ["android"]])
def test_devices_bad_filters(ctx: AppContext, args: list[str]) -> None:
    with pytest.raises(UsageError):
        ctx.registry.execute(ctx, "devices", args, CommandScope.INTERACTIVE)


def test_setup_rejects_unknown_option(ctx: AppContext) -> None:
    with pytest.raises(UsageError):
        ctx.registry.execute(ctx, "setup", ["--force"], CommandScope.DIRECT)


def test_rustdesk_errors_become_command_errors(ctx: AppContext) -> None:
    with pytest.raises(CommandError, match="RustDesk client was not found"):  # no RustDesk in the isolated profile
        ctx.registry.execute(ctx, "connect", ["326245055"], CommandScope.INTERACTIVE)


def test_aliases_resolve(ctx: AppContext) -> None:
    assert ctx.registry.resolve("quit", CommandScope.INTERACTIVE).name == "exit"
    assert ctx.registry.resolve("CLS", CommandScope.INTERACTIVE).name == "clear"


def test_duplicate_registration_is_rejected() -> None:
    registry = build_registry()
    with pytest.raises(ValueError):
        registry.register(registry.resolve("help", CommandScope.INTERACTIVE))
