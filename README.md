<p align="center"><img src="assets/logo.png" alt="EyeControl" width="520"></p>

# EyeControl

**Site : https://akm12.com/logiciels/eyecontrol** · Téléchargements : https://github.com/akm12-dev/releases ·
Guide PDF : `Guide_EyeControl-0.2.0.pdf` (dans la release)

Logiciel de télémaintenance piloté depuis le terminal : on tape `eyecontrol` dans CMD, PowerShell,
Windows Terminal (ou un terminal Linux / Kali) et la console EyeControl s'ouvre.

Objectif final : administrer des PC Windows (terminal distant + contrôle graphique), puis assister des
smartphones Android et visualiser des iPhone, depuis une seule interface — uniquement pour de l'assistance
**autorisée**, avec consentement et indicateur visible.

## État actuel — version 0.2.0

EyeControl est la console du technicien ; la prise en main (écran, souris, clavier, terminal, fichiers) est
assurée par **RustDesk**, logiciel libre, via le **serveur RustDesk d'AKM12** (`hosting.websentinelle.com`).
La personne dépannée lance le module de https://akm12.com/assistance (rien à installer) et donne son ID et
son mot de passe ; le mot de passe se saisit dans RustDesk, EyeControl ne le voit jamais.

| Commande | État |
|---|---|
| `connect <ID>`, `desktop`, `shell`, `files`, `sysinfo`, `disconnect` | ✅ via RustDesk (client installé sur le poste du technicien) |
| `devices [--type TYPE]` | ✅ historique RustDesk de ce poste |
| `setup [--write]` | ✅ réglages RustDesk du serveur AKM12 |
| `help`, `status`, `version`, `clear`, `exit` | ✅ |
| `login`, `logout`, `screen`, `control` | ⏳ pas encore disponible (« not available yet », ne fait rien) |

## Installation

### Windows 10 / 11 — version prête à l'emploi

Téléchargez `EyeControl-0.2.0-windows.zip` sur https://akm12.com/logiciels/eyecontrol, extrayez-le
(ex. `C:\Outils\EyeControl`), ajoutez ce dossier au PATH, puis tapez `eyecontrol`. Détails dans `LISEZMOI.txt`.

### Windows 10 / 11 — depuis le code source

Prérequis : Python 3.12 ou plus récent (avec « Add to PATH »).

```powershell
git clone <url-du-depot> eyecontrol
cd eyecontrol
python -m pip install -e .\cli
eyecontrol --version
```

Désinstallation : `python -m pip uninstall eyecontrol`

### Kali Linux / Debian / Ubuntu

Kali protège le Python du système (PEP 668) : on passe par **pipx**.

```bash
sudo apt install -y pipx git
pipx ensurepath          # puis rouvrir le terminal
git clone <url-du-depot> eyecontrol
pipx install -e ./eyecontrol/cli
eyecontrol --version
```

> La console est prévue pour Linux et ses tests unitaires couvrent les dossiers Linux, mais elle n'a pas
> encore été essayée sur une vraie machine Kali.

## Utilisation

Préparer le poste technicien : installer RustDesk (https://rustdesk.com), puis `eyecontrol setup` pour les
réglages du serveur (serveur ID et relais `hosting.websentinelle.com`, clé publique affichée).

```text
eyecontrol                          ouvre la console interactive
eyecontrol connect 482913507        ouvre directement la prise en main RustDesk
eyecontrol devices --type windows   PC déjà dépannés depuis ce poste
eyecontrol status                   serveur joignable ? RustDesk trouvé et bien réglé ?
eyecontrol setup                    réglages RustDesk à saisir (ou setup --write en portable)
```

Dans la console :

```text
eyecontrol > connect 482 913 507   (espaces acceptés, Tab complète les ID connus)
482913507 > shell                  terminal distant
482913507 > files                  transfert de fichiers
482913507 > desktop                rouvre l'écran distant
482913507 > disconnect
```

Raccourcis : **Tab** complète, **↑ ↓** historique, **Ctrl+C** efface la ligne, **Ctrl+D** quitte.

Codes de sortie : `0` OK · `1` erreur · `2` erreur de saisie · `3` pas encore disponible · `130` interrompu.

## Configuration

Tout est facultatif. Priorité : variables d'environnement > `config.toml` > valeurs par défaut.

| | Windows | Linux |
|---|---|---|
| Configuration | `%APPDATA%\EyeControl\config.toml` | `~/.config/eyecontrol/config.toml` |
| Journal, historique | `%LOCALAPPDATA%\EyeControl\` | `~/.local/state/eyecontrol/` |

```toml
[rustdesk]                      # facultatif : serveur AKM12 par défaut
host = "hosting.websentinelle.com"
key = "Su9SDic3OWDbKFdJoqOiItwP+Gw2Ec6OUYIfGSf5PBo="
client = 'D:\Outils\RustDesk\rustdesk.exe'   # si RustDesk n'est pas trouvé automatiquement

[logging]
level = "INFO"
```

Variables : `EYECONTROL_RUSTDESK_HOST`, `EYECONTROL_RUSTDESK_KEY`, `EYECONTROL_RUSTDESK_CLIENT`, `EYECONTROL_ENV` (`production` / `development`),
`EYECONTROL_LOG_LEVEL`, `EYECONTROL_CONFIG_DIR`, `EYECONTROL_DATA_DIR`.
Aucun mot de passe ni jeton ne va dans ce fichier.

## Développement

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".\cli[dev]"
.venv\Scripts\python -m pytest            # tests
.venv\Scripts\ruff check cli tests        # style
cd cli; ..\.venv\Scripts\mypy eyecontrol  # types
```

## Construire une version

```powershell
.venv\Scripts\python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File build_windows.ps1   # dist\ : exe, zip Windows, wheel
python docsuild\shots.py                                   # captures de la console
python docsuild\make_guide.py                              # guide PDF (Chrome requis)
```

## Licence

Code consultable, tous droits réservés : voir [LICENSE](LICENSE).

## Organisation

```text
cli/        console technicien (Python : Typer, prompt_toolkit, Rich)
server/     (non utilisé : la mise en relation passe par le serveur RustDesk d'AKM12)
agent/      agents installés sur les appareils (Rust) — agent/windows/ d'abord
mobile/     agents Android et iOS (étapes mobiles)
viewer/     fenêtre de visualisation du bureau / de l'écran
shared/     contrats communs (schéma de déclaration des appareils)
installer/  installateurs
tests/      tests automatisés
docs/       architecture, feuille de route, tests manuels
```

Voir [docs/architecture.md](docs/architecture.md), [docs/roadmap.md](docs/roadmap.md) et
[docs/testing.md](docs/testing.md).
