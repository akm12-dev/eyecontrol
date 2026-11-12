# EyeControl

Logiciel de télémaintenance piloté depuis le terminal : on tape `eyecontrol` dans CMD, PowerShell,
Windows Terminal (ou un terminal Linux / Kali) et la console EyeControl s'ouvre.

Objectif final : administrer des PC Windows (terminal distant + contrôle graphique), puis assister des
smartphones Android et visualiser des iPhone, depuis une seule interface — uniquement pour de l'assistance
**autorisée**, avec consentement et indicateur visible.

## État actuel — version 0.1.0

| Partie | État |
|---|---|
| Commande `eyecontrol` (Windows, Linux) | ✅ fonctionnelle |
| Console interactive (logo, invite, autocomplétion, historique, barre d'état) | ✅ fonctionnelle |
| `help`, `status`, `version`, `clear`, `exit` | ✅ fonctionnelles |
| `login`, `logout`, `devices` | ⏳ phase 3 (serveur et authentification) |
| `connect`, `disconnect`, `sysinfo` | ⏳ phase 4 (agent Windows) |
| `shell cmd\|powershell` | ⏳ phase 5 (terminal distant) |
| `desktop` | ⏳ phase 6 (contrôle graphique) |
| `screen`, `control` | ⏳ étapes mobiles |

Les commandes pas encore développées existent déjà (aide, autocomplétion, vérification des arguments) mais
affichent clairement **« not available yet »** et ne font rien. Aucune fonction n'est simulée.

## Installation

### Windows 10 / 11

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

```text
eyecontrol                       ouvre la console interactive
eyecontrol --version             affiche la version
eyecontrol --help                aide des commandes directes
eyecontrol status                état (serveur, technicien, fichiers)
eyecontrol devices --type ios    (phase 3) appareils filtrés par système
```

Dans la console :

```text
eyecontrol > help            liste des commandes (ready / phase prévue)
eyecontrol > help shell      détail d'une commande
eyecontrol > status
eyecontrol > exit            ou Ctrl+D
```

Raccourcis : **Tab** complète, **↑ ↓** historique, **Ctrl+C** efface la ligne, **Ctrl+D** quitte.

Certaines commandes n'ont de sens que dans la console (`connect`, `shell`, `desktop`…). Tapées directement
(`eyecontrol connect PC-001`), elles expliquent qu'il faut d'abord ouvrir la console.

Codes de sortie : `0` OK · `1` erreur · `2` erreur de saisie · `3` pas encore disponible · `130` interrompu.

## Configuration

Tout est facultatif. Priorité : variables d'environnement > `config.toml` > valeurs par défaut.

| | Windows | Linux |
|---|---|---|
| Configuration | `%APPDATA%\EyeControl\config.toml` | `~/.config/eyecontrol/config.toml` |
| Journal, historique | `%LOCALAPPDATA%\EyeControl\` | `~/.local/state/eyecontrol/` |

```toml
[server]
url = "https://eyecontrol.example.com"   # https obligatoire

[logging]
level = "INFO"
```

Variables : `EYECONTROL_SERVER_URL`, `EYECONTROL_ENV` (`production` / `development`),
`EYECONTROL_LOG_LEVEL`, `EYECONTROL_CONFIG_DIR`, `EYECONTROL_DATA_DIR`.
Aucun mot de passe ni jeton ne va dans ce fichier : ils iront dans le coffre du système (phase 3).

## Développement

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".\cli[dev]"
.venv\Scripts\python -m pytest            # tests
.venv\Scripts\ruff check cli tests        # style
cd cli; ..\.venv\Scripts\mypy eyecontrol  # types
```

## Organisation

```text
cli/        console technicien (Python : Typer, prompt_toolkit, Rich)
server/     serveur FastAPI + PostgreSQL (phase 3)
agent/      agents installés sur les appareils (Rust) — agent/windows/ d'abord
mobile/     agents Android et iOS (étapes mobiles)
viewer/     fenêtre de visualisation du bureau / de l'écran (phase 6)
shared/     contrats communs (schéma de déclaration des appareils)
installer/  installateurs (phase 8)
tests/      tests automatisés
docs/       architecture, feuille de route, tests manuels
```

Voir [docs/architecture.md](docs/architecture.md), [docs/roadmap.md](docs/roadmap.md) et
[docs/testing.md](docs/testing.md).
