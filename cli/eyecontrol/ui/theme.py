"""Colours and console factory. Sober palette: cyan accent, greys, semantic colours."""

from __future__ import annotations

import os
import sys
from typing import IO

from rich.console import Console
from rich.theme import Theme

ACCENT = "#22b8cf"

THEME = Theme(
    {
        "accent": f"bold {ACCENT}",
        "logo": ACCENT,
        "muted": "grey58",
        "label": "grey70",
        "ok": "green3",
        "warn": "yellow3",
        "err": "bold red3",
        "planned": "grey50 italic",
        "cmd": f"bold {ACCENT}",
    }
)


def make_console(file: IO[str] | None = None, *, width: int | None = None, force_terminal: bool | None = None) -> Console:
    no_color = "NO_COLOR" in os.environ
    return Console(
        file=file,
        theme=THEME,
        highlight=False,
        width=width,
        force_terminal=force_terminal,
        no_color=no_color,
    )


def supports_unicode(console: Console) -> bool:
    """True when the box-drawing logo can be written without mojibake."""
    encoding = console.encoding or getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        "█╗═║".encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def terminal_name() -> str:
    if os.environ.get("WT_SESSION"):
        return "Windows Terminal"
    if os.environ.get("TERM_PROGRAM") == "vscode":
        return "VS Code terminal"
    if os.environ.get("TERM_PROGRAM"):
        return os.environ["TERM_PROGRAM"]
    if sys.platform == "win32":
        return "Windows console (conhost)"
    return os.environ.get("TERM", "unknown")
