from __future__ import annotations

from pathlib import Path

import pytest

from eyecontrol.config import Environment, SettingsError, load_settings, validate_server_url


def env_for(tmp_path: Path, **extra: str) -> dict[str, str]:  # Windows layout
    return {"APPDATA": str(tmp_path / "roaming"), "LOCALAPPDATA": str(tmp_path / "local"), **extra}


def test_defaults_use_windows_app_folders(tmp_path: Path) -> None:
    settings = load_settings(env_for(tmp_path))
    assert settings.environment is Environment.PRODUCTION
    assert settings.config_file == tmp_path / "roaming" / "EyeControl" / "config.toml"
    assert settings.log_file == tmp_path / "local" / "EyeControl" / "logs" / "eyecontrol.log"
    assert settings.server_url is None
    assert settings.log_level == "INFO"
    assert settings.warnings == ()


def test_directory_overrides(tmp_path: Path) -> None:
    settings = load_settings({"EYECONTROL_CONFIG_DIR": str(tmp_path / "c"), "EYECONTROL_DATA_DIR": str(tmp_path / "d")})
    assert settings.config_dir == tmp_path / "c"
    assert settings.history_file == tmp_path / "d" / "history.txt"


def test_server_url_from_environment_is_normalised(tmp_path: Path) -> None:
    settings = load_settings(env_for(tmp_path, EYECONTROL_SERVER_URL=" https://ec.example.com/ "))
    assert settings.server_url == "https://ec.example.com"


def test_config_file_is_read_and_env_wins(tmp_path: Path) -> None:
    cfg = tmp_path / "roaming" / "EyeControl"
    cfg.mkdir(parents=True)
    (cfg / "config.toml").write_text('[server]\nurl = "https://file.example.com"\n[logging]\nlevel = "debug"\n', encoding="utf-8")
    assert load_settings(env_for(tmp_path)).server_url == "https://file.example.com"
    assert load_settings(env_for(tmp_path)).log_level == "DEBUG"
    overridden = load_settings(env_for(tmp_path, EYECONTROL_SERVER_URL="https://env.example.com"))
    assert overridden.server_url == "https://env.example.com"


def test_broken_config_file_becomes_a_warning(tmp_path: Path) -> None:
    cfg = tmp_path / "roaming" / "EyeControl"
    cfg.mkdir(parents=True)
    (cfg / "config.toml").write_text("[server\nurl=", encoding="utf-8")
    settings = load_settings(env_for(tmp_path))
    assert settings.server_url is None
    assert any("ignored" in w for w in settings.warnings)


def test_invalid_values_become_warnings(tmp_path: Path) -> None:
    settings = load_settings(
        env_for(tmp_path, EYECONTROL_ENV="staging", EYECONTROL_LOG_LEVEL="loud", EYECONTROL_SERVER_URL="ftp://x")
    )
    assert settings.environment is Environment.PRODUCTION
    assert settings.log_level == "INFO"
    assert settings.server_url is None
    assert len(settings.warnings) == 3


@pytest.mark.parametrize(
    "url",
    [
        "http://ec.example.com",  # clear text in production
        "https://user:pass@ec.example.com",  # credentials in URL
        "https://ec.example.com/?token=abc",  # query string
        "not a url",
        "https://[::1",  # malformed
    ],
)
def test_rejected_server_urls(url: str) -> None:
    with pytest.raises(SettingsError):
        validate_server_url(url, Environment.PRODUCTION)


def test_http_localhost_only_in_development() -> None:
    assert validate_server_url("http://localhost:8000", Environment.DEVELOPMENT) == "http://localhost:8000"
    with pytest.raises(SettingsError):
        validate_server_url("http://localhost:8000", Environment.PRODUCTION)
    with pytest.raises(SettingsError):
        validate_server_url("http://192.168.1.10:8000", Environment.DEVELOPMENT)


def test_linux_defaults_follow_xdg(tmp_path: Path) -> None:
    settings = load_settings({"HOME": str(tmp_path)}, platform="linux")
    assert settings.config_file == tmp_path / ".config" / "eyecontrol" / "config.toml"
    assert settings.log_file == tmp_path / ".local" / "state" / "eyecontrol" / "logs" / "eyecontrol.log"
    xdg = load_settings(
        {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "cfg"), "XDG_STATE_HOME": str(tmp_path / "st")},
        platform="linux",
    )
    assert xdg.config_dir == tmp_path / "cfg" / "eyecontrol"
    assert xdg.data_dir == tmp_path / "st" / "eyecontrol"
