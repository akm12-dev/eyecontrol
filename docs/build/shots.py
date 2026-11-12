"""Captures d'écran de la console EyeControl pour le guide et le site.

Le rendu est celui du vrai code (mêmes fonctions que la console), enregistré
par Rich en SVG, puis converti en PNG par Chrome sans interface.
Les chemins affichés sont neutres (profil « Technicien ») pour ne publier
aucune information personnelle.

    python docs/build/shots.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "build" / "shots"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

os.environ.update(
    {
        "EYECONTROL_CONFIG_DIR": r"C:\Users\Technicien\AppData\Roaming\EyeControl",
        "EYECONTROL_DATA_DIR": str(OUT / "_data"),
        "WT_SESSION": "shots",
    }
)
for var in ("EYECONTROL_SERVER_URL", "EYECONTROL_ENV", "EYECONTROL_LOG_LEVEL"):
    os.environ.pop(var, None)

from rich.console import Console  # noqa: E402

from eyecontrol.commands import CommandError, CommandScope, build_registry  # noqa: E402
from eyecontrol.commands.context import AppContext  # noqa: E402
from eyecontrol.config import load_settings  # noqa: E402
from eyecontrol.ui import render  # noqa: E402
from eyecontrol.ui.repl import execute_line  # noqa: E402
from eyecontrol.ui.theme import THEME  # noqa: E402

LOG_FILE = r"C:\Users\Technicien\AppData\Local\EyeControl\logs\eyecontrol.log"


def new_ctx(width: int = 96) -> AppContext:
    console = Console(record=True, width=width, theme=THEME, force_terminal=True, color_system="truecolor", highlight=False, file=open(os.devnull, "w", encoding="utf-8"))
    return AppContext(console=console, settings=load_settings(), registry=build_registry(), interactive=True, log_file=LOG_FILE)


def prompt(ctx: AppContext, line: str) -> None:
    ctx.console.print(f"[accent]{ctx.prompt_label}[/] [muted]>[/] {line}")
    execute_line(ctx, line)


def shell_line(ctx: AppContext, line: str) -> None:
    ctx.console.print(f"[muted]PS C:\\Users\\Technicien>[/] {line}")


def save(ctx: AppContext, name: str, title: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / f"{name}.svg"
    svg.write_text(ctx.console.export_svg(title=title), encoding="utf-8")
    return svg


def to_png(svg: Path) -> Path:
    text = svg.read_text(encoding="utf-8")
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    if not m:
        raise SystemExit(f"viewBox introuvable dans {svg}")
    width, height = (int(float(v)) + 1 for v in m.groups())
    html = svg.with_suffix(".html")
    html.write_text(
        f'<!doctype html><html><body style="margin:0;background:#0d1117">{text}</body></html>', encoding="utf-8"
    )
    png = svg.with_suffix(".png")
    subprocess.run(
        [
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
            f"--window-size={width},{height}", f"--screenshot={png}", html.as_uri(),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    html.unlink()
    return png


def main() -> int:
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
    prompt(ctx, "status")
    prompt(ctx, "help shell")
    shots.append(save(ctx, "etat", "EyeControl"))

    ctx = new_ctx()
    ctx.interactive = False
    shell_line(ctx, "eyecontrol --version")
    ctx.console.print("EyeControl 0.1.0")
    shell_line(ctx, "eyecontrol devices --type windows")
    try:
        ctx.registry.execute(ctx, "devices", ["--type", "windows"], CommandScope.DIRECT)
    except CommandError as exc:  # NotAvailableError attendu
        render.error(ctx.console, exc)
    shell_line(ctx, "eyecontrol connect PC-001")
    try:
        ctx.registry.execute(ctx, "connect", ["PC-001"], CommandScope.DIRECT)
    except CommandError as exc:  # UsageError attendu
        render.error(ctx.console, exc)
    shots.append(save(ctx, "commandes-directes", "Windows PowerShell"))

    for svg in shots:
        print(to_png(svg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
