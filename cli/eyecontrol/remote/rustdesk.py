"""Thin, testable wrapper around the RustDesk client on the technician's PC."""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{5,31}$")  # never starts with "-": it would be read as an option
SERVER_OPTION_KEYS = ("custom-rendezvous-server", "relay-server", "key")
RENDEZVOUS_PORT = 21116

# RustDesk "platform" values → EyeControl device types
PLATFORM_TYPES = {"windows": "windows", "linux": "linux", "mac os": "macos", "android": "android", "ios": "ios"}


class RustDeskError(Exception):
    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


@dataclass(frozen=True, slots=True)
class RustDeskServer:
    host: str
    key: str


class ClientConfigState(StrEnum):
    OK = "ok"  # client points to the EyeControl server
    NOT_CONFIGURED = "not_configured"  # no custom server: RustDesk public servers would be used
    OTHER_SERVER = "other_server"  # configured for another server or another key
    UNKNOWN = "unknown"  # no readable config file (client never started yet)


@dataclass(frozen=True, slots=True)
class KnownDevice:
    device_id: str
    hostname: str
    username: str
    platform: str
    last_seen: datetime

    @property
    def device_type(self) -> str:
        return PLATFORM_TYPES.get(self.platform.strip().lower(), "other")


def normalize_id(raw: str) -> str:
    """RustDesk shows IDs as '326 245 055': accept spaces, return '326245055'."""
    value = raw.replace(" ", "").strip()
    if not ID_PATTERN.match(value):
        raise RustDeskError(
            f"'{raw}' is not a valid RustDesk ID.",
            hint="Use the ID shown in the RustDesk window of the person you help, e.g. 326245055.",
        )
    return value


def _config_dir(env: Mapping[str, str], platform: str) -> Path:
    if platform == "win32":
        base = Path(env["APPDATA"]) if env.get("APPDATA") else Path.home() / "AppData" / "Roaming"
        return base / "RustDesk" / "config"
    base = Path(env["XDG_CONFIG_HOME"]) if env.get("XDG_CONFIG_HOME") else Path(env.get("HOME") or Path.home()) / ".config"
    return base / "rustdesk"


def _client_candidates(env: Mapping[str, str], platform: str) -> list[Path]:
    found: list[Path] = []
    if platform == "win32":
        for var in ("ProgramFiles", "ProgramW6432"):
            if env.get(var):
                found.append(Path(env[var]) / "RustDesk" / "rustdesk.exe")
        if env.get("LOCALAPPDATA"):  # unpacked portable / quick-support module
            found.append(Path(env["LOCALAPPDATA"]) / "rustdesk" / "rustdesk.exe")
    else:
        found += [Path("/usr/bin/rustdesk"), Path("/usr/local/bin/rustdesk"), Path("/opt/rustdesk/rustdesk")]
    return found


class RustDeskClient:
    """RustDesk client of the technician. All system access is injectable for tests."""

    def __init__(
        self,
        server: RustDeskServer,
        *,
        executable: str | None = None,
        env: Mapping[str, str] | None = None,
        platform: str = sys.platform,
        launcher: Callable[[Sequence[str]], object] | None = None,
        which: Callable[[str], str | None] | None = None,
    ) -> None:
        self.server = server
        self._env = os.environ if env is None else env
        self._platform = platform
        self._executable = executable
        self._launcher = launcher
        self._which = which
        self.config_dir = _config_dir(self._env, platform)

    # ---- discovery -------------------------------------------------------
    def find_executable(self) -> Path | None:
        if self._executable:
            path = Path(self._executable)
            return path if path.is_file() else None
        for candidate in _client_candidates(self._env, self._platform):
            if candidate.is_file():
                return candidate
        on_path = (self._which or shutil.which)("rustdesk")
        return Path(on_path) if on_path else None

    def require_executable(self) -> Path:
        exe = self.find_executable()
        if exe is None:
            raise RustDeskError(
                "the RustDesk client was not found on this PC.",
                hint="Install RustDesk from https://rustdesk.com, then run 'setup'.",
            )
        return exe

    # ---- configuration ---------------------------------------------------
    @property
    def config_file(self) -> Path:
        return self.config_dir / "RustDesk2.toml"

    def _read_config(self) -> dict[str, object] | None:
        try:
            with self.config_file.open("rb") as handle:
                return tomllib.load(handle)
        except FileNotFoundError:
            return None
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise RustDeskError(f"cannot read {self.config_file}: {exc}") from exc

    def config_state(self) -> ClientConfigState:
        data = self._read_config()
        if data is None:
            return ClientConfigState.UNKNOWN
        options = data.get("options")
        options = options if isinstance(options, dict) else {}
        host = str(options.get("custom-rendezvous-server", "")).strip()
        key = str(options.get("key", "")).strip()
        if not host:
            return ClientConfigState.NOT_CONFIGURED
        if host.split(":")[0].lower() == self.server.host.lower() and key == self.server.key:
            return ClientConfigState.OK
        return ClientConfigState.OTHER_SERVER

    def configure(self) -> Path | None:
        """Point the client to the EyeControl server. Returns the backup path (None if no previous file)."""
        data = self._read_config() or {}
        options = data.get("options")
        options = dict(options) if isinstance(options, dict) else {}
        options.update({"custom-rendezvous-server": self.server.host, "relay-server": self.server.host, "key": self.server.key})
        data = {**data, "options": options}
        text = _dump_simple_toml(data)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        backup = None
        if self.config_file.exists():
            backup = self.config_file.with_name(f"RustDesk2.toml.eyecontrol-{datetime.now():%Y%m%d-%H%M%S}.bak")
            shutil.copy2(self.config_file, backup)
        tmp = self.config_file.with_suffix(".toml.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self.config_file)
        return backup

    def is_running(self) -> bool:
        try:
            if self._platform == "win32":
                out = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq rustdesk.exe", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                ).stdout
                return "rustdesk.exe" in out.lower()
            return subprocess.run(["pgrep", "-x", "rustdesk"], capture_output=True, timeout=15, check=False).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    # ---- known devices (RustDesk history) --------------------------------
    def known_devices(self) -> list[KnownDevice]:
        peers = self.config_dir / "peers"
        devices: list[KnownDevice] = []
        if not peers.is_dir():
            return devices
        for file in peers.glob("*.toml"):
            try:
                with file.open("rb") as handle:
                    info = tomllib.load(handle).get("info", {})
            except (OSError, tomllib.TOMLDecodeError):
                continue
            if not isinstance(info, dict) or not ID_PATTERN.match(file.stem):
                continue
            devices.append(
                KnownDevice(
                    device_id=file.stem,
                    hostname=str(info.get("hostname", "")),
                    username=str(info.get("username", "")),
                    platform=str(info.get("platform", "")),
                    last_seen=datetime.fromtimestamp(file.stat().st_mtime),
                )
            )
        devices.sort(key=lambda d: d.last_seen, reverse=True)
        return devices

    def find_device(self, device_id: str) -> KnownDevice | None:
        return next((d for d in self.known_devices() if d.device_id == device_id), None)

    # ---- sessions --------------------------------------------------------
    def open(self, mode: str, device_id: str) -> list[str]:
        """Launch a RustDesk session window. mode: connect | terminal | file-transfer."""
        if mode not in ("connect", "terminal", "file-transfer"):
            raise ValueError(mode)
        args = [str(self.require_executable()), f"--{mode}", normalize_id(device_id)]
        try:
            (self._launcher or _spawn_detached)(args)
        except OSError as exc:
            raise RustDeskError(f"could not start RustDesk: {exc}") from exc
        return args


def server_reachable(host: str, port: int = RENDEZVOUS_PORT, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _spawn_detached(args: Sequence[str]) -> object:
    """Start RustDesk detached from the console: closing EyeControl does not close the session."""
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        return subprocess.Popen(  # noqa: S603 - fixed executable, validated arguments
            list(args), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags
        )
    return subprocess.Popen(  # noqa: S603
        list(args), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
    )


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        return "'" + value + "'" if "'" not in value and "\n" not in value else _toml_basic_string(value)
    raise RustDeskError("unexpected value type in RustDesk2.toml; nothing was changed.")


def _toml_basic_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _toml_key(key: str) -> str:
    return key if re.fullmatch(r"[A-Za-z0-9_-]+", key) else _toml_basic_string(key)


def _dump_simple_toml(data: Mapping[str, object]) -> str:
    """Serialize RustDesk2.toml: top-level scalars, then one-level tables of scalars."""
    lines: list[str] = []
    tables: list[tuple[str, Mapping[str, object]]] = []
    for key, value in data.items():
        if isinstance(value, dict):
            tables.append((key, value))
        else:
            lines.append(f"{_toml_key(key)} = {_toml_value(value)}")
    for name, table in tables:
        lines.append("")
        lines.append(f"[{_toml_key(name)}]")
        for key, value in table.items():
            if isinstance(value, dict):
                raise RustDeskError("unexpected nested table in RustDesk2.toml; nothing was changed.")
            lines.append(f"{_toml_key(key)} = {_toml_value(value)}")
    return "\n".join(lines) + "\n"
