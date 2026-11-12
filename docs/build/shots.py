"""Captures d'écran de la console EyeControl pour le guide et le site.

Le rendu est celui du vrai code (mêmes fonctions que la console), enregistré
par Rich en SVG, puis converti en PNG par Chrome sans interface.

Pour ne publier aucune information personnelle, les captures utilisent un
profil fictif « Technicien » : un faux RustDesk installé, un historique de
trois PC fictifs, et un lanceur qui n'ouvre rien.

    python docs/build/shots.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "build" / "shots"
FAKE = OUT / "_profile"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

shutil.rmtree(FAKE, ignore_errors=True)
os.environ.update(
    {
        "EYECONTROL_CONFIG_DIR": r"C:\Users\Technicien\AppData\Roaming\EyeControl",
        "EYECONTROL_DATA_DIR": str(OUT / "_data"),
        "APPDATA": str(FAKE / "Roaming"),
        "LOCALAPPDATA": str(FAKE / "Local"),
        "ProgramFiles": str(FAKE / "Program Files"),
        "ProgramW6432": str(FAKE / "Program Files"),
        "WT_SESSION": "shots",
    }
)
for var in ("EYECONTROL_SERVER_URL", "EYECONTROL_ENV", "EYECONTROL_LOG_LEVEL", "EYECONTROL_RUSTDESK_CLIENT"):
    os.environ.pop(var, None)

from rich.console import Console  # noqa: E402

from eyecontrol.commands import CommandError, CommandScope, build_registry  # noqa: E402
from eyecontrol.commands.context import AppContext  # noqa: E402
from eyecontrol.config import load_settings  # noqa: E402
from eyecontrol.remote import rustdesk as rustdesk_module  # noqa: E402
from eyecontrol.ui import render  # noqa: E402
from eyecontrol.ui.repl import execute_line  # noqa: E402
from eyecontrol.ui.theme import THEME  # noqa: E402

LOG_FILE = r"C:\Users\Technicien\AppData\Local\EyeControl\logs\eyecontrol.log"
FAKE_EXE = r"C:\Program Files\RustDesk\rustdesk.exe"
PEERS = [  # fictional devices
    ("482913507", "PC-ACCUEIL", "accueil", "Windows"),
    ("615270344", "LAPTOP-COMPTA", "compta", "Windows"),
    ("703118952", "kali", "tech", "Linux"),
]


def prepare_profile() -> None:
    exe = FAKE / "Program Files" / "RustDesk" / "rustdesk.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    cfg = FAKE / "Roaming" / "RustDesk" / "config"
    (cfg / "peers").mkdir(parents=True)
    (cfg / "RustDesk2.toml").write_text(
        "[options]\ncustom-rendezvous-server = 'hosting.websentinelle.com'\n"
        "relay-server = 'hosting.websentinelle.com'\nkey = 'Su9SDic3OWDbKFdJoqOiItwP+Gw2Ec6OUYIfGSf5PBo='\n",
        encoding="utf-8",
    )
    for i, (pid, host, user, platform) in enumerate(PEERS):
        f = cfg / "peers" / f"{pid}.toml"
        f.write_text(f"[info]\nusername = '{user}'\nhostname = '{host}'\nplatform = '{platform}'\n", encoding="utf-8")
        t = 1_794_500_000 - i * 86_400  # fixed dates (November 2026)
        os.utime(f, (t, t))
    rustdesk_module._spawn_detached = lambda args: None  # type: ignore[assignment]
    rustdesk_module.RustDeskClient.find_executable = lambda self: Path(FAKE_EXE)  # type: ignore[method-assign]
    rustdesk_module.server_reachable = lambda host, port=21116, timeout=3.0: True  # type: ignore[assignment]


def new_ctx(width: int = 96) -> AppContext:
    console = Console(
        record=True, width=width, theme=THEME, force_terminal=True, color_system="truecolor", highlight=False,
        file=open(os.devnull, "w", encoding="utf-8"),
    )
    return AppContext(console=console, settings=load_settings(), registry=build_registry(), interactive=True, log_file=LOG_FILE)


def neutral(svg_text: str) -> str:
    return svg_text.replace(str(FAKE / "Program Files" / "RustDesk" / "rustdesk.exe"), FAKE_EXE)


def prompt(ctx: AppContext, line: str) -> None:
    ctx.console.print(f"[accent]{ctx.prompt_label}[/] [muted]>[/] {line}")
    execute_line(ctx, line)


def shell_line(ctx: AppContext, line: str) -> None:
    ctx.console.print(f"[muted]PS C:\\Users\\Technicien>[/] {line}")


def save(ctx: AppContext, name: str, title: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / f"{name}.svg"
    svg.write_text(neutral(ctx.console.export_svg(title=title)), encoding="utf-8")
    return svg


def to_png(svg: Path) -> Path:
    text = svg.read_text(encoding="utf-8")
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    if not m:
        raise SystemExit(f"viewBox introuvable dans {svg}")
    width, height = (int(float(v)) + 1 for v in m.groups())
    html = svg.with_suffix(".html")
    html.write_text(f'<!doctype html><html><body style="margin:0;background:#0d1117">{text}</body></html>', encoding="utf-8")
    png = svg.with_suffix(".png")
    subprocess.run(
        [
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
            f"--window-size={width},{height}", f"--screenshot={png}", html.as_uri(),
        ],
        check=True, capture_output=True, timeout=120,
    )
    html.unlink()
    return png


def main() -> int:
    prepare_profile()
    for old in OUT.glob("*.svg"):
        old.unlink()
    for old in OUT.glob("*.png"):
        old.unlink()
    shots = []

    ctx = new_ctx()
    shell_line(ctx, "eyecontrol")
    render.banner(ctx)
    ctx.console.print("[accent]eyecontrol[/] [muted]>[/] ")
    shots.append(save(ctx, "accueil", "EyeControl"))

    ctx = new_ctx()
    prompt(ctx, "help")
    shots.append(save(ctx, "aide", "EyeControl"))

    ctx = new_ctx()
    prompt(ctx, "devices")
    prompt(ctx, "connect 482 913 507")
    prompt(ctx, "shell")
    prompt(ctx, "files")
    prompt(ctx, "disconnect")
    ctx.console.print("[accent]eyecontrol[/] [muted]>[/] ")
    shots.append(save(ctx, "session", "EyeControl"))

    ctx = new_ctx()
    ctx.interactive = False
    shell_line(ctx, "eyecontrol status")
    render.status(ctx)
    shell_line(ctx, "eyecontrol connect 615270344")
    try:
        ctx.registry.execute(ctx, "connect", ["615270344"], CommandScope.DIRECT)
    except CommandError as exc:
        render.error(ctx.console, exc)
    shots.append(save(ctx, "commandes-directes", "Windows PowerShell"))

    for svg in shots:
        print(to_png(svg))
    shutil.rmtree(FAKE, ignore_errors=True)
    shutil.rmtree(OUT / "_data", ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
