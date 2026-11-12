# Feuille de route

## Piste Windows (prioritaire)

| Phase | Contenu | État |
|---|---|---|
| 1 | Dépôt, dossiers, Python, Typer, commande `eyecontrol`, version, documentation | ✅ terminé |
| 2 | Accueil, logo, invite interactive, `help` / `status` / `exit`, erreurs et interruptions | ✅ terminé |
| 3 | Serveur FastAPI, PostgreSQL, authentification (prête pour la MFA), appareils, autorisations, audit | à faire |
| 4 | Agent Windows (Rust) : enregistrement, connexion sortante, consentement, sessions | à faire |
| 5 | Terminal distant via ConPTY : CMD et PowerShell, interruptions, redimensionnement | à faire |
| 6 | Viewer + capture (Desktop Duplication), vidéo, souris et clavier, indicateur visible | à faire |
| 7 | Internet : WebRTC, STUN/TURN, NAT, reconnexions | à faire |
| 8 | Installateurs, PATH, agent installable et désinstallable proprement, signature du code | à faire |

## Pistes suivantes (après la première version Windows)

* **Linux** : la console fonctionne déjà sous Linux/Kali. Un agent Linux (terminal bash/zsh, bureau) pourra
  réutiliser le code Rust de l'agent Windows.
* **Android** : partage d'écran, puis contrôle tactile autorisé.
* **iOS** : partage d'écran en visualisation seule.
* **Contrôle depuis un smartphone** : évolution future, non prévue pour l'instant.

Chaque étape attend une validation avant de commencer.
