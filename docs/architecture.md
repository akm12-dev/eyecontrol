# EyeControl — Architecture

> État au 12/11/2026 : phases 1 et 2 terminées (commande `eyecontrol` + console interactive).
> Aucun composant réseau n'existe encore ; les commandes prévues l'indiquent clairement.

## 1. Vue d'ensemble

```text
                 EYECONTROL CLI  (technicien)
          Windows CMD / PowerShell / Windows Terminal
                 Kali / Linux (bash, zsh)
                          |
                    HTTPS + WSS (TLS)
                          |
                  EYECONTROL SERVER
     authentification · autorisations · appareils · sessions
           signalisation · journal d'audit · révocation
                          |
      +-----------+-------+--------+-------------+
      v           v                v             v
 WINDOWS AGENT  LINUX AGENT    ANDROID AGENT   iOS AGENT
 CMD/PowerShell bash/zsh       partage écran   partage écran
 bureau+souris  bureau (X11/   gestes tactiles visualisation
 clavier        portail Wayland) (si autorisés) seule
      \           |                |             /
       +----------+---- média : WebRTC (DTLS-SRTP) ----+
                          |
                  EYECONTROL VIEWER (fenêtre)
```

Le serveur **ne fait jamais transiter de commandes à exécuter** : il authentifie, autorise, met en relation
(signalisation) et journalise. Le terminal distant et la vidéo passent dans un canal chiffré de bout en bout
entre le poste du technicien et l'agent (WebRTC ; relais TURN si les deux sont derrière des NAT).

## 2. Décisions techniques

| Sujet | Choix | Pourquoi / compromis |
|---|---|---|
| Console interactive | **prompt_toolkit + Rich** (au lieu de Textual) | Textual dessine en plein écran ; son mode « inline » n'est pas pris en charge sous Windows. Pour une expérience « à la Claude Code » (invite dans le terminal, historique de défilement conservé, sortie d'un shell distant qui défile), prompt_toolkit est l'outil adapté : édition de ligne, historique, autocomplétion, barre d'état, compatible conhost, Windows Terminal et terminaux Linux. Textual reste possible plus tard pour un écran plein (tableau de bord) si besoin. |
| Commandes directes | **Typer** | `eyecontrol status`, `--help`, `--version`. Typer et la console appellent le **même registre** (`commands/registry.py`) : une seule logique, deux portes d'entrée. |
| HTTPX / WebSockets | non ajoutés | Pas de dépendance inutilisée tant qu'il n'y a pas de serveur. |
| Serveur | FastAPI + PostgreSQL + Alembic | Conforme au cahier des charges. Signalisation par WebSocket sécurisé (WSS). |
| Agent Windows | Rust (`windows` crate) | ConPTY pour CMD/PowerShell ; Desktop Duplication API pour la capture ; un **service** (session 0) pour le système + un **processus dans la session utilisateur** pour l'écran, la souris, le clavier et l'indicateur visible. |
| Viewer | **Rust** (proposition : winit + wgpu, décodage H.264) | Même langage que l'agent → types de protocole et transport partagés ; un seul exécutable léger ; fonctionne aussi sous **Linux** (indispensable si le technicien travaille depuis Kali). Choix définitif après un prototype. |
| Média temps réel | WebRTC | Chiffrement standard (DTLS-SRTP), ICE/STUN/TURN pour les NAT. Aucun chiffrement maison. Bibliothèque (webrtc-rs ou libwebrtc) à trancher par un prototype : libwebrtc est plus mature, webrtc-rs plus simple à intégrer. |
| Secrets | coffre du système | Gestionnaire d'identification Windows, Secret Service (GNOME Keyring/KWallet) sous Linux. Jamais dans `config.toml`. |

## 3. Modèle multiplateforme

### Identité d'un appareil
* `device_id` : UUID attribué par le serveur, lié à une **paire de clés** générée sur l'appareil
  (TPM/CNG sous Windows si disponible, Android Keystore, Secure Enclave/Trousseau iOS, fichier protégé ou TPM sous Linux).
* `display_id` : alias court affiché (`PC-001`, `LX-001`, `MB-001`). Ce n'est **pas** un facteur d'authentification.

### Capacités déclarées
Chaque agent annonce ce qu'il **peut techniquement** faire, à l'enregistrement et à chaque connexion
(contrat commun : [`shared/protocol/device.schema.json`](../shared/protocol/device.schema.json), testé).

| Capacité | Windows | Linux | Android | iOS |
|---|---|---|---|---|
| `screen_view` | oui | oui (X11 ; Wayland via portail avec accord) | oui (MediaProjection, accord à chaque session) | oui (ReplayKit, lancé par l'utilisateur) |
| `remote_input` | `mouse_keyboard` | `mouse_keyboard` | `touch` (service d'accessibilité activé par l'utilisateur) | `none` — impossible avec les API publiques |
| `remote_shell` | `cmd`, `powershell` | `bash`, `zsh` | aucun | aucun |
| `sysinfo` | oui | oui | partiel | partiel |

Le schéma **refuse** les combinaisons impossibles (iPhone avec contrôle tactile, Android avec shell).

### Règle d'autorisation
Une session (et chacune de ses permissions : vue, contrôle, terminal) n'est ouverte que pour :

```text
capacités annoncées  ∩  permissions du technicien sur cet appareil  ∩  consentement de l'utilisateur distant
```

Les capacités ne donnent **jamais** un accès à elles seules. Le serveur revérifie au moment de chaque action
(ex. `control` vérifie que `remote_input` est toujours disponible et que l'utilisateur l'a accepté).

### Commandes selon l'appareil connecté
| Commande | Windows | Linux | Android | iOS |
|---|---|---|---|---|
| `shell cmd\|powershell` | oui | — (`shell bash` envisagé plus tard) | non | non |
| `desktop` | oui | oui | — | — |
| `screen` | — | — | oui | oui |
| `control` | — | — | oui si autorisé | **non pris en charge** (message explicite) |
| `sysinfo`, `disconnect` | oui | oui | oui | oui |

## 4. Organisation du dépôt

```text
eyecontrol/
├── cli/            console technicien (Python) — phases 1-2 FAITES
├── server/         serveur — retiré du plan pour l'instant
├── agent/
│   └── windows/    agent Windows (Rust)
│   (linux/ plus tard)
├── mobile/
│   ├── android/    agent Android (Kotlin) — étape Android
│   └── ios/        agent iOS (Swift) — étape iOS
├── viewer/         fenêtre de visualisation (Rust)
├── shared/
│   └── protocol/   contrats communs (schémas JSON), exemples, cas invalides
├── installer/      installateurs Windows / paquets Linux
├── tests/          tests automatisés (cli/, shared/)
└── docs/           cette documentation
```

L'agent n'existait pas encore : il est créé directement dans `agent/windows/`, donc rien n'a été déplacé.

## 5. Sécurité (dès la conception)

* TLS partout (HTTPS/WSS), WebRTC DTLS-SRTP pour le média ; aucune cryptographie maison.
* URL serveur validée : `https://` obligatoire (http seulement pour `localhost` en développement), pas d'identifiants dans l'URL.
* Jetons courts et révocables ; architecture prête pour la MFA.
* Consentement explicite pour l'assistance ponctuelle ; accès permanent seulement après inscription et autorisation de l'appareil.
* Permissions séparées : vue, contrôle, terminal.
* Indicateur visible sur l'appareil distant pendant toute session graphique ; arrêt immédiat par l'utilisateur.
* Aucune furtivité, aucun contournement UAC / root / jailbreak, aucune activation silencieuse micro ou caméra.
* Journal structuré (JSON) côté console ; **les valeurs des arguments ne sont jamais journalisées** (testé).
* Validation stricte des entrées : arguments vérifiés avant toute action, messages réseau validés par schéma.
