---
type: mcp.inject::au-mcp-sdk
name: contexte-du-repo-aefi-acquisition
description: "Ce qu'est le repo AEFI_Acquisition, comment le lancer, où vivent ses données et ses notes, et comment ses branches et worktrees bornent le travail ; remplace le CLAUDE.md du repo."
---

# Le repo AEFI_Acquisition

Ce repo est le logiciel d'acquisition du banc AEFI (Active Electric Field Imaging).
Il pilote un scan 2D avec une excitation DDS (AD9106), un ADC (ADS131A04) et un capteur électromagnétique, puis fait la détection synchrone.
Il produit les cartographies 2D de mesures du problème direct à 4 sphères.

## Lancer et tester

- Python ≥ 3.10, géré par uv : `uv run python`, `uv run pytest`
- UI en PySide6, code en DDD : `src/domain`, `src/application`, `src/infrastructure`, `src/interface`
- Application sur le matériel réel : `uv run python src/interface/main.py`
- Application tout en simulation : `uv run python src/main_mock.py`
- Logs sans l'UI : `AEFI_LOG_LEVEL=DEBUG` et `AEFI_LOG_FILE=<chemin>`
- Serveur MCP d'observabilité, en lecture seule, sur `develop` : `src/infrastructure/mcp/`, démarré à la fin de `main.py` sur `http://127.0.0.1:8765/mcp`, déclaré dans `.mcp.json` (outil `get_scan_status`)
- `conftest.py` reste à la racine : il porte le garde-fou qui sauvegarde et restaure `.aefi_acquisition/` autour des tests, et pytest n'appelle ses hooks de session que depuis la racine

## Où vivent les choses

- `_system/` : la référence des agents, à lire avant une décision d'architecture. Objectifs dans `_system/self/goals.md`, tâches dans `_system/ops/tasks.md`, raccourcis délibérés (`ponytail:`) dans `_system/ops/ponytail-debt.md`, schémas de config dans `goals.md`.
- `.aefi_acquisition/` : données d'exécution (configs, scans, calibrations, logs), hors git. Les configs matérielles de l'utilisateur sont dans `.aefi_acquisition/configs/`, leurs modèles par défaut dans `config_templates/`.
- `external_modules/` : modules tiers, dont `aefi_post_processor_module`.
- `archives/` : instantané de la première application, pas du code vivant.
- `inbox/` : notes entrantes non triées. `launch/` : scripts de lancement.
- Exports réels (scans CSV/XLSX, captures) : hors repo, dans `C:\Users\manip\Desktop\AEFI_Acquisition_Exports`, sur l'ordinateur du laboratoire seulement. En simulation, on exporte dans le dossier de travail.

## Branches et worktrees

- `main` est stable ; une release est un tag sur `main` (`v1.0.2` aujourd'hui), jamais une branche `release/*`.
- `develop` intègre ; tout nouveau développement part de `develop`.
- `feature/*` part de `develop` et se supprime une fois fusionnée.
- Un worktree `AEFI_Acquisition_dev_<contexte>` borne le travail à son contexte : on n'y touche que ce périmètre. `AEFI_Acquisition_dev` (`develop`) est l'espace partagé, où tout est modifiable. En cas de doute sur un périmètre, demander avant de toucher hors du contexte évident.
- Avant toute modification, identifier le worktree courant (`git worktree list`).
- Les anciennes branches sont conservées par les tags `v1.0.0`, `v1.0.1`, `v1.0.2` et `archive/*`.

Commits au format conventionnel : `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`.

## Notes de run, de mesure et de décision technique

Une note qui documente un run, une mesure, une acquisition ou une décision technique dans ce repo est une note hors graphe `data-note::sk-data`, rangée à côté de ce qu'elle décrit.
Ses règles sont dans [[configurations-et-runs::sk-data]].
