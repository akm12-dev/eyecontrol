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
    key = "Su9SDic3OWDbKFdJoqOiItwP+Gw2Ec6OUYIfGSf5PBo="
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
  <li>Comment fonctionne EyeControl</li>
  <li>Préparer le poste du technicien</li>
  <li>Installer EyeControl (Windows, Linux)</li>
  <li>Dépanner un PC, étape par étape</li>
  <li>Toutes les commandes</li>
  <li>Commandes directes et codes de sortie</li>
  <li>Fichiers et configuration</li>
  <li>Dépannage</li>
  <li>Désinstallation</li>
  <li>Sécurité et vérification des fichiers</li>
</ol>
<div class="note">Ce guide décrit ce que fait réellement la version {VERSION}. Les commandes encore en préparation sont
signalées comme telles, dans le guide comme dans le logiciel.</div>
</section>

<h2>1. Comment fonctionne EyeControl</h2>
<p>EyeControl est la console du technicien : on tape <code>eyecontrol</code> dans CMD, PowerShell, Windows Terminal ou un
terminal Linux, puis on travaille au clavier. La prise en main elle-même (image de l’écran, souris, clavier, terminal,
transfert de fichiers) est assurée par <b>RustDesk</b>, un logiciel libre éprouvé, et passe par le <b>serveur d’AKM12</b>
(<code>hosting.websentinelle.com</code>), pas par un service tiers.</p>
<table>
<tr><th>Qui</th><th>Ce qu’il utilise</th></tr>
<tr><td>Le technicien</td><td>EyeControl + RustDesk installé sur son poste, réglé sur le serveur AKM12</td></tr>
<tr><td>La personne dépannée</td><td>Le module d’assistance de <b>akm12.com/assistance</b> : un seul fichier à lancer, rien à installer ni à régler</td></tr>
</table>
<p>La personne lance le module, vous lit son <b>ID</b> et son <b>mot de passe</b> ; vous tapez <code>connect &lt;ID&gt;</code>
et la fenêtre RustDesk s’ouvre. Le mot de passe se saisit dans RustDesk : EyeControl ne le voit jamais.</p>
<div class="note warn">EyeControl est destiné à l’assistance <b>autorisée</b> : aucune session sans l’ID et le mot de passe
que la personne vous communique elle-même, et elle peut tout arrêter en fermant sa fenêtre.</div>

<h2>2. Préparer le poste du technicien</h2>
<ol>
<li>Installez RustDesk depuis <b>https://rustdesk.com</b> (bouton Download, version Windows ou Linux).</li>
<li>Ouvrez RustDesk › Paramètres › Réseau › « Serveur ID/Relais », puis renseignez :</li>
</ol>
<table>
<tr><td>Serveur ID</td><td><code>hosting.websentinelle.com</code></td></tr>
<tr><td>Serveur relais</td><td><code>hosting.websentinelle.com</code></td></tr>
<tr><td>Clé</td><td><code>{key}</code></td></tr>
<tr><td>Serveur API</td><td>(laisser vide)</td></tr>
</table>
<ol start="3">
<li>En bas de la fenêtre RustDesk, l’état doit indiquer « Prêt ».</li>
</ol>
<p>La commande <code>eyecontrol setup</code> rappelle ces valeurs et vérifie les réglages. Avec un RustDesk portable (non
installé), <code>eyecontrol setup --write</code> les écrit pour vous, RustDesk fermé.</p>

<h2>3. Installer EyeControl</h2>
<h3>Windows 10 / 11</h3>
<ol>
<li>Téléchargez <code>EyeControl-{VERSION}-windows.zip</code> sur akm12.com et vérifiez son empreinte (chapitre 10).</li>
<li>Extrayez-le, par exemple dans <code>C:\\Outils\\EyeControl</code>, puis ajoutez ce dossier au PATH :</li>
</ol>
<pre>[Environment]::SetEnvironmentVariable("Path",
  [Environment]::GetEnvironmentVariable("Path","User") + ";C:\\Outils\\EyeControl", "User")</pre>
<ol start="3"><li>Rouvrez le terminal et tapez <code>eyecontrol --version</code> : la réponse est <code>EyeControl {VERSION}</code>.</li></ol>
<h3>Linux (Kali, Debian, Ubuntu)</h3>
<pre>sudo apt install -y pipx
pipx ensurepath                 # puis fermer et rouvrir le terminal
pipx install ./eyecontrol-{VERSION}-py3-none-any.whl
eyecontrol --version</pre>
<div class="note">Sous Linux, EyeControl cherche RustDesk dans <code>/usr/bin/rustdesk</code> (paquet .deb officiel). La
console n’a pas encore été essayée sur une vraie machine Kali.</div>

<h2>4. Dépanner un PC, étape par étape</h2>
{shot("accueil", "Écran d’accueil : serveur AKM12, RustDesk trouvé, aucune session")}
<ol>
<li>Envoyez à la personne le lien <b>akm12.com/assistance</b>. Elle télécharge le module et l’ouvre.</li>
<li>Elle vous lit l’ID (ex. <code>482 913 507</code>) et le mot de passe affichés dans sa fenêtre RustDesk.</li>
<li>Dans EyeControl : <code>connect 482 913 507</code> (les espaces sont acceptés). La fenêtre RustDesk s’ouvre : saisissez-y
le mot de passe.</li>
<li>Pendant la session, l’invite devient <code>482913507 &gt;</code> : <code>shell</code> ouvre un terminal distant,
<code>files</code> le transfert de fichiers, <code>desktop</code> rouvre l’écran distant, <code>sysinfo</code> rappelle le nom
du PC et son système.</li>
<li>À la fin : fermez les fenêtres RustDesk, puis <code>disconnect</code>. La personne ferme son module : plus personne ne
peut se connecter.</li>
</ol>
{shot("session", "devices, connect, shell, files et disconnect")}
<p><code>devices</code> liste les PC déjà dépannés depuis votre poste (historique RustDesk : ID, nom, utilisateur, système,
dernière utilisation), filtrables avec <code>devices --type windows</code> (<code>linux</code>, <code>macos</code>,
<code>android</code>, <code>ios</code>). La touche Tab complète les ID connus.</p>

<h2>5. Toutes les commandes</h2>
{shot("aide", "La commande help")}
<table>
<tr><th>Commande</th><th>Rôle</th></tr>
<tr><td><code>connect &lt;ID&gt;</code></td><td>Ouvre la prise en main du PC dans RustDesk et démarre la session EyeControl.</td></tr>
<tr><td><code>desktop</code>, <code>shell</code>, <code>files</code></td><td>Écran distant, terminal distant, transfert de fichiers (session en cours, ou ID en argument).</td></tr>
<tr><td><code>sysinfo</code></td><td>Nom du PC, utilisateur et système enregistrés par RustDesk.</td></tr>
<tr><td><code>disconnect</code></td><td>Termine la session dans EyeControl (fermez aussi les fenêtres RustDesk).</td></tr>
<tr><td><code>devices [--type TYPE]</code></td><td>PC déjà dépannés depuis ce poste.</td></tr>
<tr><td><code>setup [--write]</code></td><td>Affiche ou écrit les réglages RustDesk du serveur AKM12.</td></tr>
<tr><td><code>status</code></td><td>Version, serveur joignable ou non, RustDesk trouvé et bien réglé, session, fichiers.</td></tr>
<tr><td><code>help</code>, <code>version</code>, <code>clear</code>, <code>exit</code></td><td>Aide, version, effacer l’écran, quitter.</td></tr>
<tr><td><code>login</code>, <code>logout</code>, <code>screen</code>, <code>control</code></td><td><i>Pas encore disponibles</i> : elles l’indiquent et ne font rien.</td></tr>
</table>
<p>Raccourcis : <b>Tab</b> complète, <b>↑ ↓</b> rappellent l’historique, <b>Ctrl+C</b> efface la ligne, <b>Ctrl+D</b> ou
<code>exit</code> quitte.</p>

<h2>6. Commandes directes et codes de sortie</h2>
<p><code>status</code>, <code>connect</code>, <code>files</code>, <code>devices</code>, <code>setup</code>, <code>help</code> et
<code>version</code> se lancent aussi sans ouvrir la console, par exemple <code>eyecontrol connect 482913507</code>.</p>
{shot("commandes-directes", "Commandes directes dans PowerShell")}
<table>
<tr><th>Code</th><th>Signification</th></tr>
<tr><td>0</td><td>Succès</td></tr><tr><td>1</td><td>Erreur (ex. RustDesk introuvable)</td></tr>
<tr><td>2</td><td>Erreur de saisie (commande inconnue, ID invalide, pas de session)</td></tr>
<tr><td>3</td><td>Commande pas encore disponible</td></tr><tr><td>130</td><td>Interrompu (Ctrl+C)</td></tr>
</table>

<h2>7. Fichiers et configuration</h2>
<table>
<tr><th></th><th>Windows</th><th>Linux</th></tr>
<tr><td>Configuration (facultative)</td><td><code>%APPDATA%\\EyeControl\\config.toml</code></td><td><code>~/.config/eyecontrol/config.toml</code></td></tr>
<tr><td>Journal et historique</td><td><code>%LOCALAPPDATA%\\EyeControl\\</code></td><td><code>~/.local/state/eyecontrol/</code></td></tr>
</table>
<p>Par défaut, EyeControl utilise le serveur AKM12. Pour un autre serveur RustDesk, ou un RustDesk installé ailleurs :</p>
<pre>[rustdesk]
host = "mon-serveur.exemple.fr"
key = "clé publique du serveur"
client = "D:\\Outils\\RustDesk\\rustdesk.exe"   # facultatif</pre>
<p>Le journal enregistre le nom des commandes lancées, jamais leurs arguments (ni les ID, ni les mots de passe).
EyeControl ne lit dans RustDesk que les réglages du serveur et la section <code>[info]</code> de l’historique (nom du PC,
utilisateur, système), jamais les mots de passe enregistrés.</p>

<h2>8. Dépannage</h2>
<table>
<tr><th>Problème</th><th>Solution</th></tr>
<tr><td>« the RustDesk client was not found »</td><td>Installez RustDesk (chapitre 2), ou indiquez son chemin dans <code>config.toml</code>.</td></tr>
<tr><td>« does not seem to use the EyeControl server »</td><td>Réglez le serveur ID, le relais et la clé (<code>eyecontrol setup</code>).</td></tr>
<tr><td>Serveur « not reachable » dans <code>status</code></td><td>Vérifiez la connexion Internet ; un pare-feu d’entreprise peut bloquer les ports 21115 à 21117.</td></tr>
<tr><td>RustDesk ne trouve pas l’ID</td><td>Le module de la personne doit être ouvert et afficher « Prêt ». Faites-vous relire l’ID.</td></tr>
<tr><td>« eyecontrol n’est pas reconnu »</td><td>Dossier absent du PATH ou terminal non rouvert.</td></tr>
<tr><td>SmartScreen bloque <code>eyecontrol.exe</code></td><td>Exécutable non signé : vérifiez l’empreinte, puis « Informations complémentaires › Exécuter quand même ».</td></tr>
</table>
<p>Contact : <b>support@akm12.com</b>, avec la sortie de <code>eyecontrol status</code>. N’envoyez jamais de mot de passe.</p>

<h2>9. Désinstallation</h2>
<ul>
<li><b>Windows</b> : supprimez le dossier d’EyeControl, retirez-le du PATH, puis supprimez <code>%APPDATA%\\EyeControl</code> et <code>%LOCALAPPDATA%\\EyeControl</code>.</li>
<li><b>Linux</b> : <code>pipx uninstall eyecontrol</code>, puis supprimez <code>~/.config/eyecontrol</code> et <code>~/.local/state/eyecontrol</code>.</li>
<li>RustDesk se désinstalle séparément (Paramètres Windows › Applications).</li>
</ul>

<h2>10. Sécurité et vérification des fichiers</h2>
<p>Chaque fichier publié est accompagné de son empreinte SHA-256 (sur akm12.com et dans <code>SHA256SUMS-eyecontrol-{VERSION}.txt</code>) :</p>
<pre>Get-FileHash .\\EyeControl-{VERSION}-windows.zip -Algorithm SHA256      # Windows
sha256sum eyecontrol-{VERSION}-py3-none-any.whl                    # Linux</pre>
<ul>
<li>Aucune session sans l’ID et le mot de passe communiqués par la personne ; la fenêtre RustDesk reste visible chez elle et elle
peut tout arrêter en la fermant.</li>
<li>Connexions chiffrées de bout en bout, via le serveur d’AKM12 ; la clé publique du serveur évite qu’un autre serveur se fasse
passer pour lui.</li>
<li>EyeControl ne contient aucune fonction cachée et ne contourne aucune protection du système.</li>
</ul>
<p style="margin-top:8mm;color:#5b6675;font-size:9pt">EyeControl {VERSION} · AKM12 – Advanced Knowledge &amp; Maintenance · https://akm12.com ·
Code consultable, tous droits réservés. RustDesk est un logiciel libre (AGPL-3.0) de ses auteurs, utilisé sans modification.</p>
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
