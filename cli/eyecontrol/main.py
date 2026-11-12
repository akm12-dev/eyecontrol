"""Entry point of the ``eyecontrol`` command.

* ``eyecontrol``               opens the interactive console
* ``eyecontrol <command> ...`` runs one command and exits (exit code reflects the result)
* ``eyecontrol --version`` / ``--help``

Exit codes: 0 ok · 1 error · 2 usage error · 3 command not available yet · 130 interrupted.
"""

# No ``from __future__ import annotations`` here: Typer evaluates the
# annotations of the per-command closures at runtime.
import sys
from typing import Annotated, Optional

import typer

from eyecontrol import APP_NAME, __version__
from eyecontrol.commands import Command, CommandError, CommandScope, ExitCode, build_registry
from eyecontrol.commands.context import AppContext
from eyecontrol.config import load_settings
from eyecontrol.encoding import configure_streams
from eyecontrol.logging_setup import configure_logging
from eyecontrol.ui import render
from eyecontrol.ui.theme import make_console


def build_context(*, interactive: bool) -> AppContext:
    settings = load_settings()
    log_file = configure_logging(settings)
    return AppContext(
        console=make_console(),
        settings=settings,
        registry=build_registry(),
        interactive=interactive,
        log_file=str(log_file) if log_file else None,
    )


def run_direct(name: str, args: list[str]) -> int:
    ctx = build_context(interactive=False)
    try:
        ctx.registry.execute(ctx, name, args, CommandScope.DIRECT)
    except CommandError as exc:
        render.error(ctx.console, exc)
        return exc.exit_code
    return ExitCode.OK


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{APP_NAME} {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="eyecontrol",
    help=f"{APP_NAME}: remote access terminal for authorized IT support.\n\n"
    "Run without arguments to open the interactive console.",
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: Annotated[
        bool, typer.Option("--version", "-V", help="Show the version and exit.", callback=_version_callback, is_eager=True)
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        from eyecontrol.ui.repl import run_interactive

        raise typer.Exit(run_interactive(build_context(interactive=True)))


def _add_direct_command(command: Command) -> None:
    help_text = command.summary if command.available else f"{command.summary} [dim](not available yet)[/dim]"

    if command.max_args == 0:

        def no_args() -> None:
            raise typer.Exit(run_direct(command.name, []))

        handler = no_args
    else:

        def with_args(
            args: Annotated[Optional[list[str]], typer.Argument(metavar=command.usage or "ARGS", show_default=False)] = None,
        ) -> None:
            raise typer.Exit(run_direct(command.name, args or []))

        handler = with_args
    # Options (e.g. devices --type android) are passed through to the registry, which validates them.
    app.command(
        name=command.name,
        help=help_text,
        context_settings={"ignore_unknown_options": True},
    )(handler)


def _add_console_only_command(command: Command) -> None:
    """Hidden entry so ``eyecontrol connect PC-001`` explains where the command belongs."""

    def console_only(ctx: typer.Context) -> None:
        raise typer.Exit(run_direct(command.name, list(ctx.args)))

    app.command(
        name=command.name,
        hidden=True,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )(console_only)


for _command in build_registry().commands():
    if _command.scope & CommandScope.DIRECT:
        _add_direct_command(_command)
    else:
        _add_console_only_command(_command)


def main() -> None:
    configure_streams()
    try:
        app()
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        sys.exit(ExitCode.INTERRUPTED)


if __name__ == "__main__":
    main()
