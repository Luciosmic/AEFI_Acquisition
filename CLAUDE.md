# AEFI Acquisition — CLAUDE.md

## Projet

Système d'acquisition pour l'AEFI (Électromagnétisme par Fluorescence d'Impédance). Pilote un banc de scan 2D avec excitation DDS (AD9106), ADC (ADS131A04), capteur électromagnétique, et post-traitement synchrone. Produit des cartographies 2D de mesures pour un problème direct 4 sphères.

## Stack

- Python ≥ 3.10, géré par **uv** (`uv run python`, `uv run pytest`)
- UI : **PySide6**
- Architecture : **DDD** (domain / application / infrastructure / interface)
- Tests : pytest (`src/_tests/`)

## Structure

```
src/
  domain/          # entités, value objects, services domaine, ports (interfaces)
  application/     # use-cases, services applicatifs, DTOs
  infrastructure/  # adaptateurs hardware (serial, AD9106, ADS131A04, moteurs Arcus)
  interface/       # UI PySide6, controllers, panneau hardware
  _tests/          # tests unitaires et intégration

_system/           # référence agents — lire en premier
_docs/             # ADR, analyses architecturales, datasheets hardware
external_modules/  # modules tiers (cube_visualizer 3D, aefi_post_processor_module)
.aefi_acquisition/ # données runtime (configs, scans, calibrations, logs) — gitignored
```

## Référence agents

Lire `_system/` avant toute décision architecturale :

- [`_system/self/goals.md`](_system/self/goals.md) — objectifs et features en cours
- [`_system/ops/tasks.md`](_system/ops/tasks.md) — tâches actives

## Branches

| Branche | Rôle |
|---------|------|
| `main` | Stable = release/v1.0.1 |
| `develop` | Intégration — base pour les nouvelles features |
| `feature/*` | Feature branch depuis develop |
| `release/v1.0.1` | Worktree `AEFI_Acquisition/` — utilisé pour les acquisitions |
| `release/v1.0.0` | Archive historique |
| `archive/ddd-refactoring` | Refactoring DDD gelé — documentation uniquement, ne pas merger |

## Contexte borné du worktree

Avant toute modification, identifier le worktree courant (nom de dossier et/ou branche git, ex. `git worktree list`) pour en déduire le contexte borné de travail :

- Worktree `_dev` (branche `develop`) → espace partagé, tout le codebase est modifiable.
- Worktree `_dev_<contexte>` (branche `dev_<contexte>`) → le suffixe `<contexte>` définit le périmètre de travail autorisé. Ne développer QUE dans ce périmètre (domaine/fichiers concernés) ; ne pas toucher aux autres parties du système. C'est ce qui permet le développement parallèle entre worktrees sans conflits.
- En cas de doute sur le périmètre exact d'un contexte borné, demander confirmation avant de modifier des fichiers hors de ce périmètre évident.

## Conventions

- Style de commit : conventionnel (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`)
- Tout nouveau développement part de `develop`
- Les configs hardware utilisateur vivent dans `.aefi_acquisition/configs/` (hors git)
- La référence des schémas de config est dans `_system/self/goals.md`
