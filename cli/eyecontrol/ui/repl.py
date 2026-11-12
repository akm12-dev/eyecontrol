"""Interactive console (``eyecontrol`` without arguments).

prompt_toolkit provides line editing, history, completion and a status
toolbar in CMD, PowerShell, Windows Terminal and Linux terminals while keeping
the normal scrollback (no full-screen takeover). Output is rendered by Rich.
When stdin is not a terminal (``type script.txt | eyecontrol``), lines are
read and executed one by one without the prompt UI.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from typing import TextIO

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory, History, InMemoryHistory
from prompt_toolkit.styles import Style

from eyecontrol.commands import CommandError, CommandScope, ExitCode, ExitRequested, parse_line
from eyecontrol.commands.context import AppContext
from eyecontrol.commands.planned import DEVICE_TYPES
from eyecontrol.logging_setup import get_logger
from eyecontrol.ui import render
from eyecontrol.ui.render import short_phase
from eyecontrol.ui.theme import ACCENT

log = get_logger("repl")

PROMPT_STYLE = Style.from_dict(
    {
        "prompt": f"bold {ACCENT}",
        "arrow": "#808080",
        "bottom-toolbar": "noreverse bg:#1f2329 #9aa0a6",
        "bottom-toolbar.key": f"bg:#1f2329 {ACCENT}",
        "bottom-toolbar.warn": "bg:#1f2329 #d7af00",
        "bottom-toolbar.ok": "bg:#1f2329 #5fd75f",
        "completion-menu.completion": "bg:#2b3036 #d0d0d0",
        "completion-menu.completion.current": f"bg:{ACCENT} #000000",
        "completion-menu.meta.completion": "bg:#2b3036 #8a8a8a",
        "completion-menu.meta.completion.current": f"bg:{ACCENT} #000000",
    }
)


class CommandCompleter(Completer):
    """Completes command names, then known argument values (help <cmd>, shell cmd|powershell, devices --type)."""

    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterator[Completion]:
        text = document.text_before_cursor.lstrip()
        words = text.split()
        completing_first = len(words) == 0 or (len(words) == 1 and not text.endswith(" "))
        registry = self._ctx.registry
        if completing_first:
            prefix = words[0].lower() if words else ""
            for command in registry.commands(CommandScope.INTERACTIVE):
                if command.name.startswith(prefix):
                    meta = (
                        command.summary
                        if command.available
                        else f"{command.summary} · {short_phase(command.planned_phase or '')}"
                    )
                    yield Completion(command.name, start_position=-len(prefix), display_meta=meta)
            return
        target = registry.get(words[0])
        if target is None:
            return
        current = "" if text.endswith(" ") else words[-1]
        position = len(words) - (0 if text.endswith(" ") else 1)  # index of the word being typed
        if target.name == "devices" and position == 2 and words[1] == "--type":
            candidates: Iterable[str] = DEVICE_TYPES
        elif position != 1:
            return
        elif target.name == "help":
            candidates = registry.names(CommandScope.INTERACTIVE)
        elif target.name == "devices":
            candidates = ("--type",)
        elif target.arg_choices:
            candidates = target.arg_choices
        else:
            return
        for value in candidates:
            if value.startswith(current.lower()):
                yield Completion(value, start_position=-len(current))


def _toolbar(ctx: AppContext) -> HTML:
    server = "<ok>configured</ok>" if ctx.settings.server_url else "<warn>not configured</warn>"
    tech = f"<ok>{ctx.technician.username}</ok>" if ctx.technician.is_authenticated else "<warn>signed out</warn>"
    session = f"<ok>{ctx.remote.device_id}</ok>" if ctx.remote else "none"
    return HTML(
        f" server: {server}  ·  technician: {tech}  ·  session: {session}"
        "    <key>Tab</key> complete  <key>↑↓</key> history  <key>Ctrl+D</key> quit "
    )


def _prompt_message(ctx: AppContext) -> HTML:
    return HTML(f"<prompt>{ctx.prompt_label}</prompt> <arrow>&gt;</arrow> ")


def execute_line(ctx: AppContext, line: str) -> tuple[bool, int]:
    """Run one console line. Returns (keep_running, exit_code)."""
    try:
        tokens = parse_line(line)
        if not tokens:
            return True, ExitCode.OK
        ctx.registry.execute(ctx, tokens[0], tokens[1:], CommandScope.INTERACTIVE)
    except ExitRequested:
        return False, ExitCode.OK
    except CommandError as exc:
        render.error(ctx.console, exc)
        return True, exc.exit_code
    except KeyboardInterrupt:
        ctx.console.print("  [warn]Interrupted.[/]")
        return True, ExitCode.INTERRUPTED
    except Exception:  # last-resort guard: the console must never crash on a command bug
        log.exception("unhandled error in command")
        where = ctx.log_file or "the log file"
        ctx.console.print(f"  [err]Internal error.[/] [muted]Details were written to {where}.[/]")
        return True, ExitCode.ERROR
    return True, ExitCode.OK


def _make_history(ctx: AppContext) -> History:
    try:
        ctx.settings.history_file.parent.mkdir(parents=True, exist_ok=True)
        return FileHistory(str(ctx.settings.history_file))
    except OSError:
        return InMemoryHistory()


def make_session(ctx: AppContext, **overrides: object) -> PromptSession[str]:
    options: dict[str, object] = {
        "history": _make_history(ctx),
        "completer": CommandCompleter(ctx),
        "complete_while_typing": True,
        "auto_suggest": AutoSuggestFromHistory(),
        "bottom_toolbar": lambda: _toolbar(ctx),
        "style": PROMPT_STYLE,
        "reserve_space_for_menu": 6,
    }
    options.update(overrides)
    return PromptSession(**options)  # type: ignore[arg-type]


def prompt_loop(ctx: AppContext, session: PromptSession[str]) -> int:
    hinted = False
    while True:
        try:
            line = session.prompt(lambda: _prompt_message(ctx))
        except KeyboardInterrupt:  # Ctrl+C at the prompt clears the line
            if not hinted:
                ctx.console.print("  [muted]Type 'exit' or press Ctrl+D to quit.[/]")
                hinted = True
            continue
        except EOFError:  # Ctrl+D
            break
        keep_running, _ = execute_line(ctx, line)
        if not keep_running:
            break
    ctx.console.print("  [muted]Session closed. Goodbye.[/]")
    return ExitCode.OK


def line_loop(ctx: AppContext, stream: TextIO) -> int:
    """Non-interactive mode: execute each line of ``stream``; return the last command's exit code."""
    code = ExitCode.OK
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        ctx.console.print(f"[accent]{ctx.prompt_label}[/] [muted]>[/] {line}", highlight=False, markup=True)
        keep_running, code = execute_line(ctx, line)
        if not keep_running:
            break
    return code


def run_interactive(ctx: AppContext) -> int:
    render.banner(ctx)
    log.info("console started", extra={"fields": {"tty": sys.stdin.isatty()}})
    if not sys.stdin.isatty():
        return line_loop(ctx, sys.stdin)
    return prompt_loop(ctx, make_session(ctx))
