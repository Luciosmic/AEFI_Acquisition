# AEFI Acquisition — CLAUDE.md

## Projet

Système d'acquisition pour l'AEFI (Active Electric Field Imaging). Pilote un banc de scan 2D avec excitation DDS (AD9106), ADC (ADS131A04), capteur électromagnétique, et post-traitement synchrone. Produit des cartographies 2D de mesures pour un problème direct 4 sphères.

## Stack

- Python ≥ 3.10, géré par **uv** (`uv run python`, `uv run pytest`)
- UI : **PySide6**
- Architecture : **DDD** (domain / application / infrastructure / interface)
- Tests : pytest (`src/_tests/`)
- Lancement : `uv run python src/main.py` (matériel réel) ; `uv run python src/main_mock.py` (dev, tout mocké)
- Logs de debug : `AEFI_LOG_LEVEL=DEBUG` et `AEFI_LOG_FILE=<chemin>` (lisibles sans l'UI)
- Serveur MCP d'observabilité (`develop` uniquement, lecture seule) : `src/infrastructure/mcp/`, démarré en thread à la fin de `main.py`, `http://127.0.0.1:8765/mcp`, déclaré dans `.mcp.json` (`aefi-observability`, tool `get_scan_status`)

## Structure

```
src/
  domain/          # entités, value objects, services domaine, ports (interfaces)
  application/     # use-cases, services applicatifs, DTOs
  infrastructure/  # adaptateurs hardware (serial, AD9106, ADS131A04, moteurs Arcus)
  interface/       # UI PySide6, controllers, panneau hardware
  _tests/          # tests unitaires et intégration

_system/           # référence agents — lire en premier
external_modules/  # modules tiers (aefi_post_processor_module)
.aefi_acquisition/ # données runtime (configs, scans, calibrations, logs) — gitignored
archives/          # anciens docs/tests archivés (_INBOX, docs, tests_e2e)
config_templates/  # templates JSON de configuration hardware par défaut
inbox/             # notes entrantes non triées (réunions, etc.)
launch/            # scripts de lancement de l'application (bat/ps1/sh/vbs)
```

## Exports de données réelles 

Les données exportées (scans CSV/XLSX, captures d'écran) vivent hors repo dans `C:\Users\manip\Desktop\AEFI_Acquisition_Exports`
Ceci est vrai uniquement pour l'ordinateur du laboratoire, qui exporte des données réelles.
En mode Mock, on exporte dans le répertoire de travail pour développement plus rapide.

## Référence agents

Lire `_system/` avant toute décision architecturale :

- [`_system/self/goals.md`](_system/self/goals.md) — objectifs et features en cours
- [`_system/ops/tasks.md`](_system/ops/tasks.md) — tâches actives
- [`_system/ops/ponytail-debt.md`](_system/ops/ponytail-debt.md) — raccourcis délibérés (`ponytail:`) à surveiller/nettoyer

## Branches

| Branche                     | Rôle                                                            |
| --------------------------- | ---------------------------------------------------------------- |
| `main`                    | Stable. Une release = un tag sur `main` (`v1.0.2` actuellement), pas une branche `release/*` |
| `develop`                 | Intégration — base pour les nouvelles features                 |
| `feature/*`               | Feature branch depuis develop, supprimée une fois fusionnée     |
| `dev_<contexte>`          | Worktree `AEFI_Acquisition_dev_<contexte>/` — développement borné à un contexte cohésif (ex. `dev_detection_devices`) |
| `archive/bar-lidar-calibration` | Calibration de la transmission par barre + LIDAR, abandonnée le 2026-10-30 au profit de la caractérisation autonome Banc-test-II dans `Hardware - Caracterisation` ; corrections générales récupérées dans develop via `feature/lidar-esp32-and-fixes` |

Les anciennes branches (releases, refactoring DDD, sauvegarde pré-rollback, POC n8n) ont été supprimées le 2026-10-30. Leur contenu utile est conservé par les tags `v1.0.0`, `v1.0.1`, `v1.0.2` et `archive/*`.

## Contexte borné du worktree

Avant toute modification, identifier le worktree courant (nom de dossier et/ou branche git, ex. `git worktree list`) pour en déduire le contexte borné de travail :

- Worktree `_dev` (branche `develop`) → espace partagé, tout le codebase est modifiable.
- Worktree `_dev_<contexte>` (branche `dev_<contexte>`) → le suffixe `<contexte>` définit le périmètre de travail autorisé. Ne développer QUE dans ce périmètre (domaine/fichiers concernés) ; ne pas toucher aux autres parties du système. C'est ce qui permet le développement parallèle entre worktrees sans conflits.
- En cas de doute sur le périmètre exact d'un contexte borné, demander confirmation avant de modifier des fichiers hors de ce périmètre évident.

## Conventions

- Style de commit : conventionnel (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`)
- Tout nouveau développement part de `develop`
- Les configs hardware runtime utilisateur vivent dans `.aefi_acquisition/configs/` (hors git)
- La référence des schémas de config est dans `_system/self/goals.md`

---

## Documentation locale — notes hors-graphe

Toute note documentant un run, une mesure, une acquisition ou une décision technique
dans ce dossier suit la convention **hors-graphe** de la thèse :

@../../_system/manual/convention-des-notes-hors-graphe.md
