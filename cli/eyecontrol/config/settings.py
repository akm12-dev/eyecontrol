"""Settings for the EyeControl CLI.

Precedence: environment variables > ``config.toml`` > built-in defaults.

Environment variables
---------------------
EYECONTROL_ENV          ``production`` (default) or ``development``
EYECONTROL_SERVER_URL   URL of the EyeControl server (``https://`` required;
                        ``http://`` accepted only for localhost in development)
EYECONTROL_LOG_LEVEL    DEBUG, INFO (default), WARNING or ERROR
EYECONTROL_CONFIG_DIR   overrides the config folder
EYECONTROL_DATA_DIR     overrides the data folder (logs, history)

Default folders
---------------
Windows  %APPDATA%\\EyeControl                %LOCALAPPDATA%\\EyeControl
Linux    $XDG_CONFIG_HOME/eyecontrol         $XDG_STATE_HOME/eyecontrol
         (~/.config/eyecontrol)              (~/.local/state/eyecontrol)

No secret is ever read from or written to ``config.toml``: from phase 3,
credentials and tokens are stored in the OS keyring (Windows Credential
Manager, Secret Service on Linux).
"""

from __future__ import annotations

import os
import sys
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlsplit

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class SettingsError(ValueError):
    """Invalid configuration value."""


@dataclass(frozen=True, slots=True)
class Settings:
    environment: Environment
    config_dir: Path
    data_dir: Path
    server_url: str | None
    log_level: str
    warnings: tuple[str, ...] = ()

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.toml"

    @property
    def log_file(self) -> Path:
        return self.data_dir / "logs" / "eyecontrol.log"

    @property
    def history_file(self) -> Path:
        return self.data_dir / "history.txt"


def validate_server_url(url: str, environment: Environment) -> str:
    """Return the normalised server URL or raise :class:`SettingsError`."""
    value = url.strip()
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
    except ValueError as exc:  # e.g. malformed IPv6 literal
        raise SettingsError(f"invalid server URL: {exc}") from exc
    if parts.scheme not in ("https", "http") or not hostname:
        raise SettingsError("server URL must look like https://server.example.com")
    if parts.username or parts.password:
        raise SettingsError("server URL must not contain credentials")
    if parts.query or parts.fragment:
        raise SettingsError("server URL must not contain a query string or fragment")
    if parts.scheme == "http" and not (environment is Environment.DEVELOPMENT and hostname in LOCAL_HOSTS):
        raise SettingsError("server URL must use https:// (http:// is only accepted for localhost in development)")
    return value.rstrip("/")


def _default_dirs(env: Mapping[str, str], platform: str) -> tuple[Path, Path]:
    home = Path(env.get("USERPROFILE") or env.get("HOME") or Path.home())
    if platform == "win32":
        config = Path(env["APPDATA"]) if env.get("APPDATA") else home / "AppData" / "Roaming"
        data = Path(env["LOCALAPPDATA"]) if env.get("LOCALAPPDATA") else home / "AppData" / "Local"
        return config / "EyeControl", data / "EyeControl"
    config = Path(env["XDG_CONFIG_HOME"]) if env.get("XDG_CONFIG_HOME") else home / ".config"
    data = Path(env["XDG_STATE_HOME"]) if env.get("XDG_STATE_HOME") else home / ".local" / "state"
    return config / "eyecontrol", data / "eyecontrol"


def _read_config_file(path: Path) -> tuple[dict[str, object], list[str]]:
    if not path.is_file():
        return {}, []
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle), []
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {}, [f"{path} ignored: {exc}"]


def load_settings(env: Mapping[str, str] | None = None, platform: str = sys.platform) -> Settings:
    """Build :class:`Settings`. Invalid values become warnings, never crashes."""
    env = os.environ if env is None else env
    warnings: list[str] = []

    raw_env = env.get("EYECONTROL_ENV", Environment.PRODUCTION).strip().lower()
    try:
        environment = Environment(raw_env)
    except ValueError:
        warnings.append(f"EYECONTROL_ENV={raw_env!r} is not valid; using 'production'")
        environment = Environment.PRODUCTION

    default_config, default_data = _default_dirs(env, platform)
    config_dir = Path(env["EYECONTROL_CONFIG_DIR"]) if env.get("EYECONTROL_CONFIG_DIR") else default_config
    data_dir = Path(env["EYECONTROL_DATA_DIR"]) if env.get("EYECONTROL_DATA_DIR") else default_data

    file_data, file_warnings = _read_config_file(config_dir / "config.toml")
    warnings.extend(file_warnings)
    server_section = file_data.get("server", {})
    logging_section = file_data.get("logging", {})
    file_url = server_section.get("url") if isinstance(server_section, dict) else None
    file_level = logging_section.get("level") if isinstance(logging_section, dict) else None

    server_url: str | None = None
    raw_url = env.get("EYECONTROL_SERVER_URL") or (file_url if isinstance(file_url, str) else None)
    if raw_url:
        try:
            server_url = validate_server_url(raw_url, environment)
        except SettingsError as exc:
            warnings.append(f"server URL ignored: {exc}")

    raw_level = (env.get("EYECONTROL_LOG_LEVEL") or (file_level if isinstance(file_level, str) else "") or "INFO").upper()
    if raw_level not in LOG_LEVELS:
        warnings.append(f"log level {raw_level!r} is not valid; using INFO")
        raw_level = "INFO"

    return Settings(
        environment=environment,
        config_dir=config_dir,
        data_dir=data_dir,
        server_url=server_url,
        log_level=raw_level,
        warnings=tuple(warnings),
    )
