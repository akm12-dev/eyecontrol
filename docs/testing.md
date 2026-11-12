# Tests

## Automatiques

```powershell
.venv\Scripts\python -m pytest
```

| Fichier | Ce qui est vérifié |
|---|---|
| `tests/cli/test_settings.py` | dossiers Windows et Linux, priorités, URL serveur (https, pas d'identifiants), fichier invalide |
| `tests/cli/test_registry.py` | découpage des lignes, commandes inconnues, console vs terminal, arguments, `devices --type` |
| `tests/cli/test_repl.py` | bannière, aide, erreurs, Ctrl+C, journal sans arguments, autocomplétion, vraie session prompt_toolkit simulée |
| `tests/cli/test_main.py` | `--version`, `--help`, commandes directes et codes de sortie |
| `tests/cli/test_smoke_windows.py` | l'exécutable installé lancé depuis CMD et PowerShell (ignoré s'il n'est pas dans le PATH) |
| `tests/shared/test_device_schema.py` | le schéma commun accepte les exemples et refuse les combinaisons impossibles |

## Manuels (console réelle)

À faire dans **CMD**, **Windows PowerShell 5.1**, **Windows Terminal** et un terminal **Kali** :

1. `eyecontrol` : le logo et les couleurs s'affichent, l'invite `eyecontrol >` apparaît, la barre d'état est en bas.
2. Taper `st` puis **Tab** → `status` ; **↑** rappelle la commande précédente.
3. `shell ` puis **Tab** → propose `cmd` et `powershell`.
4. **Ctrl+C** sur une ligne commencée : la ligne s'efface, la console reste ouverte.
5. `desktop` → message « Not available ».
6. Redimensionner la fenêtre : l'affichage suit.
7. `exit` (ou **Ctrl+D**) → « Session closed. Goodbye. »
