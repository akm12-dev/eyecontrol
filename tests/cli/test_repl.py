from __future__ import annotations

import io
import json
import logging

from prompt_toolkit.application import create_app_session
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from eyecontrol.commands import ExitCode
from eyecontrol.commands.context import AppContext
from eyecontrol.logging_setup import configure_logging
from eyecontrol.ui import render
from eyecontrol.ui.repl import CommandCompleter, execute_line, line_loop, make_session, prompt_loop


def completions(ctx: AppContext, text: str) -> list[str]:
    return [c.text for c in CommandCompleter(ctx).get_completions(Document(text), CompleteEvent())]


def test_banner_shows_honest_state(ctx: AppContext, output: io.StringIO) -> None:
    render.banner(ctx)
    text = output.getvalue()
    assert "E Y E C O N T R O L" in text
    assert "Remote Access Terminal" in text
    assert "not configured" in text
    assert "not signed in" in text
    assert "Connected" not in text and "signed in as" not in text  # nothing is connected in this version


def test_help_lists_ready_and_planned(ctx: AppContext, output: io.StringIO) -> None:
    assert execute_line(ctx, "help") == (True, ExitCode.OK)
    text = output.getvalue()
    assert "shell cmd|powershell" in text
    assert "ready" in text and "planned" in text
    assert "phase" not in text.lower()


def test_status_command(ctx: AppContext, output: io.StringIO) -> None:
    assert execute_line(ctx, "status") == (True, ExitCode.OK)
    text = output.getvalue()
    assert "EyeControl 0.1.0" in text
    assert "Config file" in text


def test_exit_stops_the_loop(ctx: AppContext) -> None:
    assert execute_line(ctx, "exit") == (False, ExitCode.OK)
    assert execute_line(ctx, "quit") == (False, ExitCode.OK)


def test_errors_are_rendered_not_raised(ctx: AppContext, output: io.StringIO) -> None:
    assert execute_line(ctx, "frobnicate") == (True, ExitCode.USAGE)
    assert execute_line(ctx, "desktop") == (True, ExitCode.NOT_AVAILABLE)
    assert execute_line(ctx, 'connect "PC') == (True, ExitCode.USAGE)
    text = output.getvalue()
    assert "unknown command 'frobnicate'" in text
    assert "Not available" in text


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


def test_command_log_never_contains_arguments(ctx: AppContext) -> None:
    configure_logging(ctx.settings)
    execute_line(ctx, "connect SECRET-VALUE")
    logging.getLogger("eyecontrol").handlers[0].flush()
    content = ctx.settings.log_file.read_text(encoding="utf-8")
    assert '"command": "connect"' in content
    assert "SECRET-VALUE" not in content


def test_completer(ctx: AppContext) -> None:
    assert completions(ctx, "st") == ["status"]
    assert set(completions(ctx, "")) >= {"help", "connect", "desktop"}
    assert completions(ctx, "shell ") == ["cmd", "powershell"]
    assert completions(ctx, "shell p") == ["powershell"]
    assert "desktop" in completions(ctx, "help d")
    assert completions(ctx, "status ") == []
    assert completions(ctx, "shell cmd ") == []
    assert completions(ctx, "devices ") == ["--type"]
    assert completions(ctx, "devices --type a") == ["android"]
    assert {"screen", "control"} <= set(completions(ctx, ""))


def test_line_loop_runs_until_exit(ctx: AppContext, output: io.StringIO) -> None:
    code = line_loop(ctx, io.StringIO("help\n\nshell bash\nexit\nstatus\n"))
    text = output.getvalue()
    assert code == ExitCode.OK
    assert "eyecontrol > shell bash" in text
    assert "Environment" not in text  # 'status' after 'exit' is never executed


def test_line_loop_returns_last_exit_code(ctx: AppContext) -> None:
    assert line_loop(ctx, io.StringIO("status\ndevices\n")) == ExitCode.NOT_AVAILABLE


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
    assert "EyeControl 0.1.0" in text  # status ran
    assert "Type 'exit' or press Ctrl+D to quit." in text
    assert "shell cmd|powershell" in text
    assert "Goodbye" in text
