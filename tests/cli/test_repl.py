from __future__ import annotations

import io
import json
import logging
import re
from pathlib import Path

from prompt_toolkit.application import create_app_session
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from eyecontrol import __version__
from eyecontrol.commands import ExitCode
from eyecontrol.commands.context import AppContext
from eyecontrol.logging_setup import configure_logging
from eyecontrol.ui import render
from eyecontrol.ui.repl import CommandCompleter, execute_line, line_loop, make_session, prompt_loop


def completions(ctx: AppContext, text: str) -> list[str]:
    return [c.text for c in CommandCompleter(ctx).get_completions(Document(text), CompleteEvent())]


def add_peer(ctx: AppContext, device_id: str, hostname: str, platform: str = "Windows") -> None:
    peers = ctx.rustdesk.config_dir / "peers"
    peers.mkdir(parents=True, exist_ok=True)
    (peers / f"{device_id}.toml").write_text(
        f"[info]\nusername = 'user'\nhostname = '{hostname}'\nplatform = '{platform}'\n", encoding="utf-8"
    )


def test_banner_shows_honest_state(ctx: AppContext, output: io.StringIO) -> None:
    render.banner(ctx)
    text = output.getvalue()
    assert "E Y E C O N T R O L" in text and "Remote Access Terminal" in text
    assert "hosting.websentinelle.com" in text
    assert "not found: install RustDesk" in text  # no RustDesk in the isolated profile
    assert "Session" in text and "none" in text


def test_banner_with_rustdesk(ctx: AppContext, output: io.StringIO, rustdesk_exe: Path) -> None:
    render.banner(ctx)
    assert re.search(r"RustDesk\s+found", output.getvalue())


def test_help_lists_ready_and_planned(ctx: AppContext, output: io.StringIO) -> None:
    assert execute_line(ctx, "help") == (True, ExitCode.OK)
    text = output.getvalue()
    assert "connect <device-id>" in text and "setup [--write]" in text
    assert "ready" in text and "planned" in text


def test_status_command(ctx: AppContext, output: io.StringIO, rustdesk_exe: Path) -> None:
    assert execute_line(ctx, "status") == (True, ExitCode.OK)
    text = output.getvalue()
    assert f"EyeControl {__version__}" in text
    assert "(reachable)" in text and "RustDesk path" in text
    assert "no settings file yet" in text


def test_full_session_flow(ctx: AppContext, output: io.StringIO, rustdesk_exe: Path, launches) -> None:
    add_peer(ctx, "326245055", "LAPTOP-ANNE")
    assert execute_line(ctx, "connect 326 245 055") == (True, ExitCode.OK)
    assert ctx.prompt_label == "326245055"
    assert ctx.remote is not None and ctx.remote.computer_name == "LAPTOP-ANNE"
    for line in ("shell", "files", "desktop", "sysinfo"):
        assert execute_line(ctx, line) == (True, ExitCode.OK)
    assert [call[1:] for call in launches.calls] == [
        ["--connect", "326245055"],
        ["--terminal", "326245055"],
        ["--file-transfer", "326245055"],
        ["--connect", "326245055"],
    ]
    assert execute_line(ctx, "disconnect") == (True, ExitCode.OK)
    assert ctx.remote is None and ctx.prompt_label == "eyecontrol"
    text = output.getvalue()
    assert "Opening remote desktop in RustDesk for 326245055 (LAPTOP-ANNE)..." in text
    assert "EyeControl never sees it" in text and "LAPTOP-ANNE" in text


def test_session_commands_need_a_session(ctx: AppContext, rustdesk_exe: Path, launches) -> None:
    for line in ("shell", "files", "desktop", "sysinfo", "disconnect"):
        assert execute_line(ctx, line) == (True, ExitCode.USAGE)
    assert launches.calls == []


def test_connect_rejects_bad_ids_without_launching(ctx: AppContext, rustdesk_exe: Path, launches) -> None:
    assert execute_line(ctx, 'connect "326245055 & calc"') == (True, ExitCode.ERROR)
    assert launches.calls == []


def test_connect_warns_when_client_uses_public_servers(ctx: AppContext, output: io.StringIO, rustdesk_exe: Path) -> None:
    cfg = ctx.rustdesk.config_file
    cfg.parent.mkdir(parents=True)
    cfg.write_text("rendezvous_server = 'rs-ny.rustdesk.com:21116'\n[options]\n", encoding="utf-8")
    execute_line(ctx, "connect 326245055")
    assert "does not seem to use the EyeControl server" in output.getvalue()


def test_devices_lists_history_and_filters(ctx: AppContext, output: io.StringIO) -> None:
    assert execute_line(ctx, "devices") == (True, ExitCode.OK)
    assert "No device yet" in output.getvalue()
    add_peer(ctx, "111222333", "LAPTOP-ANNE", "Windows")
    add_peer(ctx, "444555666", "kali", "Linux")
    output.truncate(0)
    output.seek(0)
    assert execute_line(ctx, "devices --type linux") == (True, ExitCode.OK)
    text = output.getvalue()
    assert "444555666" in text and "kali" in text and "111222333" not in text


def test_setup_shows_values_then_writes(ctx: AppContext, output: io.StringIO, rustdesk_exe: Path, monkeypatch) -> None:
    assert execute_line(ctx, "setup") == (True, ExitCode.OK)
    text = output.getvalue()
    assert "hosting.websentinelle.com" in text and ctx.settings.rustdesk_key in text
    assert not ctx.rustdesk.config_file.exists()  # showing values never writes
    monkeypatch.setattr(type(ctx.rustdesk), "is_running", lambda self: True)
    assert execute_line(ctx, "setup --write") == (True, ExitCode.ERROR)
    assert "RustDesk is running" in output.getvalue()
    monkeypatch.setattr(type(ctx.rustdesk), "is_running", lambda self: False)
    assert execute_line(ctx, "setup --write") == (True, ExitCode.OK)
    assert "EyeControl server configured" in (render_status := (execute_line(ctx, "status"), output.getvalue()))[1]
    assert render_status[0] == (True, ExitCode.OK)


def test_exit_stops_the_loop(ctx: AppContext) -> None:
    assert execute_line(ctx, "exit") == (False, ExitCode.OK)
    assert execute_line(ctx, "quit") == (False, ExitCode.OK)


def test_errors_are_rendered_not_raised(ctx: AppContext, output: io.StringIO) -> None:
    assert execute_line(ctx, "frobnicate") == (True, ExitCode.USAGE)
    assert execute_line(ctx, "screen") == (True, ExitCode.NOT_AVAILABLE)
    assert execute_line(ctx, 'connect "PC') == (True, ExitCode.USAGE)
    assert execute_line(ctx, "connect 326245055") == (True, ExitCode.ERROR)  # RustDesk not installed
    text = output.getvalue()
    assert "unknown command 'frobnicate'" in text
    assert "Not available" in text
    assert "RustDesk client was not found" in text


def test_unexpected_exception_is_contained_and_logged(ctx: AppContext, output: io.StringIO, monkeypatch) -> None:
    configure_logging(ctx.settings)

    def boom(*_args: object) -> None:
        raise RuntimeError("bug")

    monkeypatch.setattr(ctx.registry, "execute", boom)
    assert execute_line(ctx, "status") == (True, ExitCode.ERROR)
    assert "Internal error" in output.getvalue()
    logging.getLogger("eyecontrol").handlers[0].flush()
    records = [json.loads(line) for line in ctx.settings.log_file.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["level"] == "ERROR" and "RuntimeError: bug" in records[-1]["exc"]


def test_keyboard_interrupt_during_command(ctx: AppContext, output: io.StringIO, monkeypatch) -> None:
    def interrupted(*_args: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(ctx.registry, "execute", interrupted)
    assert execute_line(ctx, "status") == (True, ExitCode.INTERRUPTED)
    assert "Interrupted" in output.getvalue()


def test_command_log_never_contains_arguments(ctx: AppContext, rustdesk_exe: Path) -> None:
    configure_logging(ctx.settings)
    execute_line(ctx, "connect 987654321")
    logging.getLogger("eyecontrol").handlers[0].flush()
    content = ctx.settings.log_file.read_text(encoding="utf-8")
    assert '"command": "connect"' in content
    assert "987654321" not in content


def test_completer(ctx: AppContext) -> None:
    add_peer(ctx, "326245055", "LAPTOP-ANNE")
    add_peer(ctx, "444555666", "kali", "Linux")
    assert completions(ctx, "st") == ["status"]
    assert set(completions(ctx, "")) >= {"help", "connect", "desktop", "files", "setup"}
    assert completions(ctx, "connect 32") == ["326245055"]
    assert set(completions(ctx, "shell ")) == {"326245055", "444555666"}
    assert "desktop" in completions(ctx, "help d")
    assert completions(ctx, "status ") == []
    assert completions(ctx, "devices ") == ["--type"]
    assert completions(ctx, "devices --type a") == ["android"]


def test_line_loop_runs_until_exit(ctx: AppContext, output: io.StringIO) -> None:
    code = line_loop(ctx, io.StringIO("help\n\nshell\nexit\nstatus\n"))
    text = output.getvalue()
    assert code == ExitCode.OK
    assert "eyecontrol > shell" in text
    assert "Environment" not in text  # 'status' after 'exit' is never executed


def test_line_loop_returns_last_exit_code(ctx: AppContext) -> None:
    assert line_loop(ctx, io.StringIO("status\nlogin\n")) == ExitCode.NOT_AVAILABLE


def test_prompt_loop_with_real_prompt_toolkit_session(ctx: AppContext, output: io.StringIO) -> None:
    """Drives the actual PromptSession with simulated keystrokes (Enter, Ctrl+C, Ctrl+D).

    Tab completion is asynchronous in prompt_toolkit, so it is covered by test_completer instead.
    """
    with create_pipe_input() as pipe, create_app_session(input=pipe, output=DummyOutput()):
        session = make_session(ctx, input=pipe, output=DummyOutput())
        pipe.send_text("status\r")
        pipe.send_text("\x03")  # Ctrl+C at the prompt: clears the line, does not quit
        pipe.send_text("help shell\r")
        pipe.send_text("\x04")  # Ctrl+D on an empty line: quit
        code = prompt_loop(ctx, session)
    text = output.getvalue()
    assert code == ExitCode.OK
    assert f"EyeControl {__version__}" in text  # status ran
    assert "Type 'exit' or press Ctrl+D to quit." in text
    assert "shell [device-id]" in text
    assert "Goodbye" in text
