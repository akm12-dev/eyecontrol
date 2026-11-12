"""RustDesk integration: discovery, settings file, history, command lines. Nothing real is started."""

from __future__ import annotations

import os
import time
import tomllib
from pathlib import Path

import pytest

from eyecontrol.remote import ClientConfigState, RustDeskClient, RustDeskError, RustDeskServer, normalize_id
from eyecontrol.remote.rustdesk import _dump_simple_toml

SERVER = RustDeskServer("hosting.websentinelle.com", "Su9SDic3OWDbKFdJoqOiItwP+Gw2Ec6OUYIfGSf5PBo=")


def client(tmp_path: Path, **kwargs: object) -> RustDeskClient:
    env = {"APPDATA": str(tmp_path / "Roaming"), "LOCALAPPDATA": str(tmp_path / "Local"), "ProgramFiles": str(tmp_path / "PF")}
    return RustDeskClient(SERVER, env=env, platform="win32", which=lambda _: None, **kwargs)  # type: ignore[arg-type]


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("raw", "expected"), [("326245055", "326245055"), ("326 245 055", "326245055"), ("pc-office_1", "pc-office_1")]
)
def test_normalize_id(raw: str, expected: str) -> None:
    assert normalize_id(raw) == expected


@pytest.mark.parametrize("raw", ["", "12345", "326245055; calc", "--connect", "-326245055", "a" * 40, "326/245"])
def test_invalid_ids_are_rejected(raw: str) -> None:
    with pytest.raises(RustDeskError):
        normalize_id(raw)


def test_executable_discovery_order(tmp_path: Path) -> None:
    c = client(tmp_path)
    assert c.find_executable() is None
    portable = write(tmp_path / "Local" / "rustdesk" / "rustdesk.exe", "x")
    assert c.find_executable() == portable
    installed = write(tmp_path / "PF" / "RustDesk" / "rustdesk.exe", "x")
    assert c.find_executable() == installed  # installed client first
    custom = write(tmp_path / "custom" / "rd.exe", "x")
    assert client(tmp_path, executable=str(custom)).find_executable() == custom


def test_missing_client_gives_install_hint(tmp_path: Path) -> None:
    with pytest.raises(RustDeskError) as info:
        client(tmp_path).open("connect", "326245055")
    assert "rustdesk.com" in (info.value.hint or "")


def test_open_builds_exact_command_lines(tmp_path: Path) -> None:
    exe = write(tmp_path / "PF" / "RustDesk" / "rustdesk.exe", "x")
    calls: list[list[str]] = []
    c = client(tmp_path, launcher=calls.append)
    c.open("connect", "326 245 055")
    c.open("terminal", "326245055")
    c.open("file-transfer", "326245055")
    assert calls == [
        [str(exe), "--connect", "326245055"],
        [str(exe), "--terminal", "326245055"],
        [str(exe), "--file-transfer", "326245055"],
    ]
    with pytest.raises(ValueError):
        c.open("install", "326245055")


def test_config_states(tmp_path: Path) -> None:
    c = client(tmp_path)
    assert c.config_state() is ClientConfigState.UNKNOWN
    write(c.config_file, "rendezvous_server = 'rs-ny.rustdesk.com:21116'\n[options]\n")
    assert c.config_state() is ClientConfigState.NOT_CONFIGURED
    write(c.config_file, "[options]\ncustom-rendezvous-server = 'other.example.com'\nkey = 'x'\n")
    assert c.config_state() is ClientConfigState.OTHER_SERVER
    write(c.config_file, f"[options]\ncustom-rendezvous-server = 'hosting.websentinelle.com:21116'\nkey = '{SERVER.key}'\n")
    assert c.config_state() is ClientConfigState.OK


def test_configure_keeps_other_values_and_backs_up(tmp_path: Path) -> None:
    c = client(tmp_path)
    write(c.config_file, "rendezvous_server = 'rs-ny.rustdesk.com:21116'\nnat_type = 1\nserial = 0\n\n[options]\nlang = 'fr'\n")
    backup = c.configure()
    assert backup is not None and backup.exists()
    data = tomllib.loads(c.config_file.read_text(encoding="utf-8"))
    assert data["nat_type"] == 1 and data["rendezvous_server"] == "rs-ny.rustdesk.com:21116"
    assert data["options"] == {
        "lang": "fr",
        "custom-rendezvous-server": SERVER.host,
        "relay-server": SERVER.host,
        "key": SERVER.key,
    }
    assert c.config_state() is ClientConfigState.OK


def test_configure_without_previous_file(tmp_path: Path) -> None:
    c = client(tmp_path)
    assert c.configure() is None
    assert c.config_state() is ClientConfigState.OK


def test_dump_refuses_unexpected_structures() -> None:
    with pytest.raises(RustDeskError):
        _dump_simple_toml({"options": {"nested": {"a": 1}}})
    with pytest.raises(RustDeskError):
        _dump_simple_toml({"list": [1, 2]})
    assert tomllib.loads(_dump_simple_toml({"a": "it's", "b": True, "t": {"k": 'q"x'}})) == {
        "a": "it's",
        "b": True,
        "t": {"k": 'q"x'},
    }


def test_known_devices_from_history(tmp_path: Path) -> None:
    c = client(tmp_path)
    peers = c.config_dir / "peers"
    older = write(
        peers / "111222333.toml", "password = [1, 2]\n[info]\nusername = 'anne'\nhostname = 'LAPTOP-ANNE'\nplatform = 'Windows'\n"
    )
    write(peers / "444555666.toml", "[info]\nusername = 'root'\nhostname = 'kali'\nplatform = 'Linux'\n")
    write(peers / "broken.toml", "not = [valid")
    write(peers / "bad id!.toml", "[info]\nhostname = 'x'\n")
    old = time.time() - 3600
    os.utime(older, (old, old))
    devices = c.known_devices()
    assert [d.device_id for d in devices] == ["444555666", "111222333"]  # most recent first
    assert devices[1].hostname == "LAPTOP-ANNE" and devices[1].device_type == "windows"
    assert devices[0].device_type == "linux"
    assert c.find_device("111222333") is not None and c.find_device("999999999") is None
