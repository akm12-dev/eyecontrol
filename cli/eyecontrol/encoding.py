"""Output encoding when stdout/stderr is not a terminal (pipe, redirection).

In a real console Python writes Unicode and everything displays. When output
is redirected (``eyecontrol status | more``, ``> file.txt``), Python defaults
to the ANSI code page (cp1252) while CMD and PowerShell 5.1 decode with the
console code page (often cp850), which garbles non-ASCII characters such as
the logo. The encoding is therefore aligned on the console code page.
"""

from __future__ import annotations

import sys
from typing import TextIO


def console_output_encoding() -> str:
    """Encoding expected by the attached Windows console, or UTF-8 (Linux, no console)."""
    if sys.platform != "win32":
        return "utf-8"
    import ctypes

    code_page = ctypes.windll.kernel32.GetConsoleOutputCP()
    if code_page in (0, 65001):  # 0: no console attached
        return "utf-8"
    return f"cp{code_page}"


def configure_streams(streams: tuple[TextIO, ...] = ()) -> None:
    for stream in streams or (sys.stdout, sys.stderr):
        if not hasattr(stream, "reconfigure"):
            continue
        try:
            if stream.isatty():
                stream.reconfigure(errors="replace")
            else:
                stream.reconfigure(encoding=console_output_encoding(), errors="replace")
        except (OSError, ValueError, LookupError):
            pass
