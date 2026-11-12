"""Génère le guide d'utilisation PDF d'EyeControl.

    python docs/build/shots.py        (captures, une fois)
    python docs/build/make_guide.py   -> docs/build/out/Guide_EyeControl-<version>.pdf

Le guide est écrit en HTML puis imprimé en PDF par Chrome sans interface.
"""

from __future__ import annotations

import base64
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "docs" / "build"
SHOTS = BUILD / "shots"
OUT = BUILD / "out"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

VERSION = re.search(r'__version__ = "(.+)"', (ROOT / "cli" / "eyecontrol" / "__init__.py").read_text(encoding="utf-8")).group(1)
DATE = "12 novembre 2026"


def img(path: Path) -> str:
    mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def shot(name: str, caption: str) -> str:
    return f'<figure><img src="{img(SHOTS / (name + ".png"))}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'


CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
@page :first { margin: 0; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; color: #1b2430; font-size: 10.5pt; line-height: 1.5; margin: 0; }
h1 { font-size: 20pt; margin: 0 0 4mm; color: #0b1622; }
h2 { font-size: 14pt; margin: 9mm 0 3mm; color: #0a5fdb; border-bottom: 1.5px solid #d6e4fb; padding-bottom: 1.5mm; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 5mm 0 2mm; break-after: avoid; }
p, li { margin: 0 0 2mm; }
ul, ol { padding-left: 6mm; margin: 0 0 3mm; }
code, pre { font-family: Consolas, "Cascadia Mono", monospace; font-size: 9.5pt; }
code { background: #eef2f7; padding: 0 1.2mm; border-radius: 3px; }
pre { background: #0d1117; color: #e6edf3; padding: 3mm 4mm; border-radius: 6px; white-space: pre-wrap; break-inside: avoid; margin: 0 0 3mm; }
figure { margin: 3mm 0 5mm; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 120mm; border-radius: 6px; }
figcaption { font-size: 9pt; color: #5b6675; margin-top: 1.5mm; }
table { border-collapse: collapse; width: 100%; margin: 0 0 4mm; break-inside: avoid; font-size: 9.8pt; }
th, td { border: 1px solid #d5dce6; padding: 1.6mm 2.4mm; text-align: left; vertical-align: top; }
th { background: #f1f5fb; }
.note { border-left: 4px solid #0a5fdb; background: #f1f6ff; padding: 2.5mm 4mm; margin: 0 0 4mm; break-inside: avoid; }
.warn { border-left-color: #c98a00; background: #fff8e6; }
.cover { height: 296mm; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
         background: #000; color: #e6edf3; margin: 0; padding: 0 20mm; break-after: page; }
.cover img { width: 150mm; }
.cover .t { font-size: 22pt; font-weight: 600; margin-top: 6mm; color: #fff; }
.cover .s { font-size: 12pt; color: #9fb3c8; margin-top: 2mm; }
.cover .m { font-size: 10pt; color: #7f93a8; margin-top: 18mm; }
.toc ol { font-size: 11pt; } .toc li { margin-bottom: 1.5mm; }
"""


def build_html() -> str:
    logo = img(ROOT / "assets" / "logo.png")
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Guide EyeControl {VERSION}</title><style>{CSS}</style></head><body>

<section class="cover">
  <img src="{logo}" alt="EyeControl">
  <div class="t">Guide d’utilisation</div>
  <div class="s">Console de télémaintenance dans le terminal · version {VERSION}</div>
  <div class="m">AKM12 · Par un tech, pour les tech. · akm12.com · {DATE}</div>
</section>

<section class="toc" style="break-after: page">
<h1>Sommaire</h1>
<ol>
  <li>Présentation et état de la version {VERSION}</li>
  <li>Installation sous Windows</li>
  <li>Installation sous Linux (Kali, Debian, Ubuntu)</li>
  <li>Premier lancement</li>
  <li>La console interactive</li>
  <li>Commandes directes et codes de sortie</li>
  <li>État, fichiers et configuration</li>
  <li>Dépannage</li>
  <li>Désinstallation</li>
  <li>Sécurité et vérification des fichiers</li>
</ol>
<div class="note">Ce guide décrit uniquement ce que fait réellement la version {VERSION}. Les fonctions qui ne sont pas encore
développées sont signalées comme telles, dans le guide comme dans le logiciel.</div>
</section>

<h2>1. Présentation et état de la version {VERSION}</h2>
<p>EyeControl est une console de télémaintenance qui s’ouvre <b>directement dans le terminal</b> : on tape
<code>eyecontrol</code> dans CMD, PowerShell, Windows Terminal ou un terminal Linux, et l’interface EyeControl
apparaît, avec son invite <code>eyecontrol &gt;</code>. Aucune fenêtre, aucun navigateur.</p>
<p>La version {VERSION} pose la base du logiciel : la commande, la console interactive et toutes les commandes prévues,
avec leur aide et la vérification de leurs arguments.</p>
<table>
<tr><th>Disponible</th><th>Pas encore disponible</th></tr>
<tr><td><code>help</code>, <code>status</code>, <code>version</code>, <code>clear</code>, <code>exit</code><br>
<code>eyecontrol --version</code>, <code>eyecontrol --help</code><br>autocomplétion, historique, barre d’état</td>
<td><code>login</code>, <code>logout</code>, <code>devices</code>, <code>connect</code>, <code>disconnect</code>,
<code>sysinfo</code>, <code>shell</code>, <code>desktop</code>, <code>screen</code>, <code>control</code></td></tr>
</table>
<div class="note warn">Les commandes « pas encore disponibles » affichent <code>Not available … is not available yet</code>
et <b>ne font rien</b> : rien n’est envoyé ni exécuté. La version {VERSION} ne se connecte à aucun ordinateur.</div>

<h2>2. Installation sous Windows</h2>
<h3>Avec l’archive (recommandé)</h3>
<ol>
<li>Téléchargez <code>EyeControl-{VERSION}-windows.zip</code> depuis akm12.com et vérifiez son empreinte SHA-256 (chapitre 10).</li>
<li>Extrayez l’archive dans un dossier, par exemple <code>C:\\Outils\\EyeControl</code>.</li>
<li>Ajoutez ce dossier au PATH de votre compte, dans PowerShell :</li>
</ol>
<pre>[Environment]::SetEnvironmentVariable("Path",
  [Environment]::GetEnvironmentVariable("Path","User") + ";C:\\Outils\\EyeControl", "User")</pre>
<ol start="4">
<li>Fermez puis rouvrez le terminal et tapez <code>eyecontrol --version</code> : la réponse doit être <code>EyeControl {VERSION}</code>.</li>
</ol>
<p>Sans toucher au PATH, vous pouvez aussi lancer directement <code>C:\\Outils\\EyeControl\\eyecontrol.exe</code>.</p>
<h3>Avec Python (pour les développeurs)</h3>
<p>Si Python 3.12 ou plus récent est installé, le paquet <code>eyecontrol-{VERSION}-py3-none-any.whl</code> s’installe avec :</p>
<pre>python -m pip install eyecontrol-{VERSION}-py3-none-any.whl</pre>

<h2>3. Installation sous Linux (Kali, Debian, Ubuntu)</h2>
<p>Kali protège le Python du système : on installe EyeControl avec <b>pipx</b>, dans un environnement isolé.</p>
<pre>sudo apt install -y pipx
pipx ensurepath                 # puis fermer et rouvrir le terminal
pipx install ./eyecontrol-{VERSION}-py3-none-any.whl
eyecontrol --version</pre>
<div class="note">La console est prévue pour Linux et ses tests automatiques couvrent les dossiers Linux, mais elle n’a pas
encore été essayée sur une vraie machine Kali. Merci de signaler tout problème (chapitre 8).</div>

<h2>4. Premier lancement</h2>
<p>Tapez <code>eyecontrol</code> dans le terminal. L’écran d’accueil affiche le logo, la version et l’état :
serveur, technicien et session. En version {VERSION}, ils sont toujours <i>not configured</i>, <i>not signed in</i>
et <i>none</i>, ce qui est normal.</p>
{shot("accueil", "Écran d’accueil d’EyeControl dans Windows PowerShell")}

<h2>5. La console interactive</h2>
<p>À l’invite <code>eyecontrol &gt;</code>, tapez une commande puis Entrée. La commande <code>help</code> liste toutes
les commandes : celles marquées <b>ready</b> fonctionnent, celles marquées <i>planned</i> ne sont pas encore disponibles.</p>
{shot("aide", "La commande help : commandes prêtes (ready) et prévues (planned)")}
<h3>Raccourcis clavier</h3>
<table>
<tr><th>Touche</th><th>Effet</th></tr>
<tr><td>Tab</td><td>Complète le nom de la commande ou de son argument (ex. <code>shell p</code> → <code>powershell</code>).</td></tr>
<tr><td>↑ / ↓</td><td>Rappelle les commandes précédentes (historique conservé d’une session à l’autre).</td></tr>
<tr><td>Ctrl+C</td><td>Efface la ligne en cours, sans quitter.</td></tr>
<tr><td>Ctrl+D ou <code>exit</code></td><td>Quitte EyeControl.</td></tr>
</table>
<h3>Commandes disponibles</h3>
<table>
<tr><th>Commande</th><th>Rôle</th></tr>
<tr><td><code>help</code></td><td>Liste les commandes. <code>help &lt;commande&gt;</code> affiche l’usage et l’état d’une commande.</td></tr>
<tr><td><code>status</code></td><td>Version, environnement, serveur, technicien, session, chemins des fichiers, terminal, système.</td></tr>
<tr><td><code>version</code></td><td>Affiche la version.</td></tr>
<tr><td><code>clear</code> (ou <code>cls</code>)</td><td>Efface l’écran.</td></tr>
<tr><td><code>exit</code> (ou <code>quit</code>)</td><td>Quitte la console.</td></tr>
</table>
<p>Les arguments sont vérifiés même pour les commandes pas encore disponibles : <code>shell bash</code> est refusé
(seuls <code>cmd</code> et <code>powershell</code> sont acceptés), <code>devices --type</code> n’accepte que
<code>windows</code>, <code>linux</code>, <code>android</code> ou <code>ios</code>.</p>

<h2>6. Commandes directes et codes de sortie</h2>
<p>Certaines commandes se lancent sans ouvrir la console, directement depuis le terminal :
<code>eyecontrol status</code>, <code>eyecontrol help</code>, <code>eyecontrol version</code>,
<code>eyecontrol --version</code> et <code>eyecontrol --help</code>. Les commandes de session
(<code>connect</code>, <code>shell</code>, <code>desktop</code>…) ne s’utilisent que dans la console : tapées directement,
elles l’expliquent.</p>
{shot("commandes-directes", "Commandes directes dans PowerShell")}
<p>Le code de sortie permet d’utiliser EyeControl dans un script :</p>
<table>
<tr><th>Code</th><th>Signification</th></tr>
<tr><td>0</td><td>Succès</td></tr><tr><td>1</td><td>Erreur</td></tr>
<tr><td>2</td><td>Erreur de saisie (commande inconnue, argument invalide)</td></tr>
<tr><td>3</td><td>Commande pas encore disponible</td></tr><tr><td>130</td><td>Interrompu (Ctrl+C)</td></tr>
</table>
<p>On peut aussi enchaîner des commandes : <code>type commandes.txt | eyecontrol</code> exécute chaque ligne du fichier.</p>

<h2>7. État, fichiers et configuration</h2>
{shot("etat", "status et help shell")}
<table>
<tr><th></th><th>Windows</th><th>Linux</th></tr>
<tr><td>Configuration (facultative)</td><td><code>%APPDATA%\\EyeControl\\config.toml</code></td><td><code>~/.config/eyecontrol/config.toml</code></td></tr>
<tr><td>Journal et historique</td><td><code>%LOCALAPPDATA%\\EyeControl\\</code></td><td><code>~/.local/state/eyecontrol/</code></td></tr>
</table>
<p>Le journal (<code>logs\\eyecontrol.log</code>, 5 fichiers de 1 Mo au maximum) enregistre le nom des commandes lancées,
jamais leurs arguments. Le fichier <code>config.toml</code> n’est pas nécessaire en version {VERSION} ; il accepte :</p>
<pre>[logging]
level = "INFO"        # DEBUG, INFO, WARNING ou ERROR</pre>
<p>Variables d’environnement reconnues : <code>EYECONTROL_LOG_LEVEL</code>, <code>EYECONTROL_ENV</code>
(<code>production</code> ou <code>development</code>), <code>EYECONTROL_CONFIG_DIR</code> et <code>EYECONTROL_DATA_DIR</code>
(pour déplacer les dossiers). Une valeur invalide est signalée par un avertissement, sans bloquer le logiciel.</p>

<h2>8. Dépannage</h2>
<table>
<tr><th>Problème</th><th>Solution</th></tr>
<tr><td>« eyecontrol n’est pas reconnu… »</td><td>Le dossier n’est pas dans le PATH, ou le terminal n’a pas été rouvert.
Rouvrez-le, ou lancez <code>eyecontrol.exe</code> avec son chemin complet.</td></tr>
<tr><td>Windows SmartScreen bloque le lancement</td><td>L’exécutable n’est pas encore signé. Vérifiez l’empreinte SHA-256 (chapitre 10),
puis <b>Informations complémentaires › Exécuter quand même</b>. Ne désactivez pas votre antivirus.</td></tr>
<tr><td>Le logo s’affiche en caractères simples</td><td>Le terminal ne gère pas les caractères spéciaux : EyeControl bascule
automatiquement sur un logo simple. Windows Terminal affiche le logo complet.</td></tr>
<tr><td>« Not available »</td><td>Normal : la commande n’est pas encore développée. Rien n’a été exécuté.</td></tr>
<tr><td>Linux : <code>eyecontrol: command not found</code></td><td>Lancez <code>pipx ensurepath</code>, puis rouvrez le terminal.</td></tr>
</table>
<p>Pour signaler un problème : <b>https://github.com/akm12-dev/releases/issues</b> ou <b>support@akm12.com</b>, en précisant
la sortie de <code>eyecontrol status</code> et le message exact. N’envoyez jamais de mot de passe.</p>

<h2>9. Désinstallation</h2>
<ul>
<li><b>Archive Windows</b> : supprimez le dossier d’EyeControl, retirez-le du PATH (Paramètres › Système › Informations système ›
Paramètres avancés › Variables d’environnement), puis supprimez <code>%APPDATA%\\EyeControl</code> et <code>%LOCALAPPDATA%\\EyeControl</code>.</li>
<li><b>Python</b> : <code>python -m pip uninstall eyecontrol</code>.</li>
<li><b>Linux</b> : <code>pipx uninstall eyecontrol</code>, puis supprimez <code>~/.config/eyecontrol</code> et <code>~/.local/state/eyecontrol</code>.</li>
</ul>

<h2>10. Sécurité et vérification des fichiers</h2>
<p>Chaque fichier publié est accompagné de son empreinte SHA-256 (sur akm12.com et dans <code>SHA256SUMS-eyecontrol-{VERSION}.txt</code>).
Vérifiez-la avant le premier lancement :</p>
<pre>Get-FileHash .\\EyeControl-{VERSION}-windows.zip -Algorithm SHA256      # Windows
sha256sum eyecontrol-{VERSION}-py3-none-any.whl                    # Linux</pre>
<p>EyeControl est destiné exclusivement à l’assistance et à l’administration <b>autorisées</b>. Ses principes, qui
s’appliqueront à toutes les fonctions futures : consentement explicite de la personne assistée, indicateur visible
pendant une session, arrêt possible à tout moment, aucune fonction cachée, aucun contournement des protections du système.</p>
<p style="margin-top:8mm;color:#5b6675;font-size:9pt">EyeControl {VERSION} · AKM12 – Advanced Knowledge &amp; Maintenance · https://akm12.com ·
Code consultable, tous droits réservés.</p>
</body></html>"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    html = OUT / "guide.html"
    html.write_text(build_html(), encoding="utf-8")
    pdf = OUT / f"Guide_EyeControl-{VERSION}.pdf"
    subprocess.run(
        [str(CHROME), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", html.as_uri()],
        check=True, capture_output=True, timeout=180,
    )
    print(pdf, pdf.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
