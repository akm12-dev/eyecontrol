"""Remote-support commands, implemented by driving the RustDesk client of the technician."""

from __future__ import annotations

from collections.abc import Sequence
from functools import wraps

from rich.table import Table
from rich.text import Text

from eyecontrol.commands.context import AppContext
from eyecontrol.commands.registry import Command, CommandError, CommandScope, Handler, Registry, UsageError
from eyecontrol.network import RemoteSession
from eyecontrol.remote import ClientConfigState, RustDeskError, normalize_id

DEVICE_TYPES = ("windows", "linux", "macos", "android", "ios")


def _rustdesk_errors(func: Handler) -> Handler:
    @wraps(func)
    def wrapper(ctx: AppContext, args: Sequence[str]) -> None:
        try:
            func(ctx, args)
        except RustDeskError as exc:
            raise CommandError(exc.message, hint=exc.hint) from exc

    return wrapper


def validate_devices_args(args: Sequence[str]) -> None:
    """Accepts nothing, or ``--type <windows|linux|macos|android|ios>``."""
    if not args:
        return
    if len(args) != 2 or args[0] != "--type":
        raise UsageError("unknown option for 'devices'.")
    if args[1].lower() not in DEVICE_TYPES:
        raise UsageError(f"unknown device type '{args[1]}' (expected: {', '.join(DEVICE_TYPES)}).")


def validate_setup_args(args: Sequence[str]) -> None:
    if args and list(args) != ["--write"]:
        raise UsageError("unknown option for 'setup'.")


def _warn_if_not_configured(ctx: AppContext) -> None:
    state = ctx.rustdesk.config_state()
    if state in (ClientConfigState.NOT_CONFIGURED, ClientConfigState.OTHER_SERVER):
        ctx.console.print(
            "  [warn]Your RustDesk client does not seem to use the EyeControl server.[/]"
            " [muted]Run 'setup' if the connection fails.[/]"
        )


def _current_or_given_id(ctx: AppContext, args: Sequence[str], command: str) -> str:
    if args:
        return normalize_id("".join(args))
    if ctx.remote:
        return ctx.remote.device_id
    raise UsageError(f"no active session for '{command}'.", hint="Run 'connect <device-id>' first, or give the device ID.")


def _open(ctx: AppContext, mode: str, device_id: str, what: str) -> None:
    ctx.rustdesk.open(mode, device_id)
    device = ctx.rustdesk.find_device(device_id)
    name = f" ({device.hostname})" if device and device.hostname else ""
    ctx.console.print(f"  [ok]Opening {what} in RustDesk for {device_id}{name}...[/]")
    ctx.console.print("  [muted]Enter the password given by the person in the RustDesk window. EyeControl never sees it.[/]")


@_rustdesk_errors
def _connect(ctx: AppContext, args: Sequence[str]) -> None:
    device_id = normalize_id("".join(args))
    _warn_if_not_configured(ctx)
    _open(ctx, "connect", device_id, "remote desktop")
    if ctx.interactive:
        device = ctx.rustdesk.find_device(device_id)
        ctx.remote = RemoteSession(
            device_id=device_id, computer_name=device.hostname if device and device.hostname else "unknown"
        )
        ctx.console.print("  [muted]Session commands: desktop, shell, files, sysinfo, disconnect.[/]")


def _disconnect(ctx: AppContext, args: Sequence[str]) -> None:
    if ctx.remote is None:
        raise UsageError("there is no active session.")
    device_id = ctx.remote.device_id
    ctx.remote = None
    ctx.console.print(f"  Session with {device_id} closed in EyeControl.")
    ctx.console.print("  [muted]Close the RustDesk window(s) to end the remote connection itself.[/]")


@_rustdesk_errors
def _desktop(ctx: AppContext, args: Sequence[str]) -> None:
    _open(ctx, "connect", _current_or_given_id(ctx, args, "desktop"), "remote desktop")


@_rustdesk_errors
def _shell(ctx: AppContext, args: Sequence[str]) -> None:
    _open(ctx, "terminal", _current_or_given_id(ctx, args, "shell"), "remote terminal")


@_rustdesk_errors
def _files(ctx: AppContext, args: Sequence[str]) -> None:
    _open(ctx, "file-transfer", _current_or_given_id(ctx, args, "files"), "file transfer")


@_rustdesk_errors
def _devices(ctx: AppContext, args: Sequence[str]) -> None:
    devices = ctx.rustdesk.known_devices()
    if args:
        devices = [d for d in devices if d.device_type == args[1].lower()]
    if not devices:
        ctx.console.print("  [muted]No device yet. Devices appear here after a first RustDesk connection.[/]")
        return
    table = Table(box=None, padding=(0, 2), header_style="label", pad_edge=False)
    for column in ("ID", "COMPUTER", "USER", "SYSTEM", "LAST USED"):
        table.add_column(column, no_wrap=True)
    for d in devices:
        active = ctx.remote is not None and ctx.remote.device_id == d.device_id
        table.add_row(
            Text(d.device_id, style="ok" if active else "cmd"),
            d.hostname or "-",
            d.username or "-",
            d.platform or "-",
            d.last_seen.strftime("%Y-%m-%d %H:%M"),
        )
    ctx.console.print()
    ctx.console.print(table)
    ctx.console.print("\n  [muted]From the RustDesk history of this PC. Online status is shown in RustDesk.[/]\n")


@_rustdesk_errors
def _sysinfo(ctx: AppContext, args: Sequence[str]) -> None:
    device_id = _current_or_given_id(ctx, args, "sysinfo")
    device = ctx.rustdesk.find_device(device_id)
    if device is None:
        raise CommandError(
            f"no information yet for {device_id}.", hint="RustDesk records it after a first successful connection."
        )
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="label")
    grid.add_column()
    grid.add_row("ID", device.device_id)
    grid.add_row("Computer", device.hostname or "-")
    grid.add_row("User", device.username or "-")
    grid.add_row("System", device.platform or "-")
    grid.add_row("Last used", device.last_seen.strftime("%Y-%m-%d %H:%M"))
    ctx.console.print()
    ctx.console.print(grid)
    ctx.console.print("\n  [muted]Information recorded by RustDesk at the last connection.[/]\n")


@_rustdesk_errors
def _setup(ctx: AppContext, args: Sequence[str]) -> None:
    client, server = ctx.rustdesk, ctx.rustdesk.server
    exe = client.find_executable()
    state = client.config_state()
    ctx.console.print()
    ctx.console.print(f"  RustDesk client   {exe or Text('not found: install it from https://rustdesk.com', style='warn')}")
    ctx.console.print(f"  Client settings   {state_label(state)}")
    if args:  # --write
        if client.is_running():
            raise CommandError(
                "RustDesk is running.", hint="Quit RustDesk (also from the notification area), then run 'setup --write' again."
            )
        backup = client.configure()
        ctx.console.print(f"\n  [ok]Settings written to {client.config_file}.[/]")
        if backup:
            ctx.console.print(f"  [muted]Previous file saved as {backup.name}.[/]")
        ctx.console.print(
            "  [muted]If RustDesk is installed as a service, also check Settings › Network in the RustDesk window.[/]\n"
        )
        return
    ctx.console.print("\n  In RustDesk: Settings › Network › ID/Relay server, then enter:\n")
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="label")
    grid.add_column(style="cmd")
    grid.add_row("    ID server", server.host)
    grid.add_row("    Relay server", server.host)
    grid.add_row("    Key", server.key)
    grid.add_row("    API server", Text("(leave empty)", style="muted"))
    ctx.console.print(grid)
    ctx.console.print(
        "\n  [muted]Portable RustDesk only: 'setup --write' writes these settings for you (RustDesk must be closed).[/]\n"
    )


def state_label(state: ClientConfigState) -> Text:
    return {
        ClientConfigState.OK: Text("EyeControl server configured", style="ok"),
        ClientConfigState.NOT_CONFIGURED: Text("RustDesk public servers (not the EyeControl server)", style="warn"),
        ClientConfigState.OTHER_SERVER: Text("another server or another key", style="warn"),
        ClientConfigState.UNKNOWN: Text("no settings file yet (start RustDesk once)", style="muted"),
    }[state]


def register_remote(registry: Registry) -> None:
    console_only = CommandScope.INTERACTIVE
    registry.register(
        Command(
            "connect",
            "Open a remote desktop session with a device (RustDesk ID)",
            _connect,
            usage="<device-id>",
            min_args=1,
            max_args=4,
            category="Session",
        )
    )
    registry.register(
        Command(
            "desktop",
            "Reopen the remote desktop window",
            _desktop,
            usage="[device-id]",
            max_args=4,
            scope=console_only,
            category="Session",
        )
    )
    registry.register(
        Command(
            "shell",
            "Open a remote terminal on the device",
            _shell,
            usage="[device-id]",
            max_args=4,
            scope=console_only,
            category="Session",
        )
    )
    registry.register(
        Command("files", "Open the file transfer window", _files, usage="[device-id]", max_args=4, category="Session")
    )
    registry.register(
        Command(
            "sysinfo",
            "Show what is known about the device",
            _sysinfo,
            usage="[device-id]",
            max_args=4,
            scope=console_only,
            category="Session",
        )
    )
    registry.register(
        Command("disconnect", "Close the current session in EyeControl", _disconnect, scope=console_only, category="Session")
    )
    registry.register(
        Command(
            "devices",
            "List devices already helped (TYPE: windows, linux, macos, android, ios)",
            _devices,
            usage="[--type TYPE]",
            max_args=2,
            validator=validate_devices_args,
            category="Devices",
        )
    )
    registry.register(
        Command(
            "setup",
            "Configure or check the RustDesk client for the EyeControl server",
            _setup,
            usage="[--write]",
            max_args=1,
            validator=validate_setup_args,
            category="Devices",
        )
    )
