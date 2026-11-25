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

## Règles apprises au banc

Corrections de l'humain, reprises le 2026-11-16 de la mémoire native de Claude du PC du labo.

1. **Tests hors du checkout réel.** Jamais de `pytest` dans `C:\Users\manip\AEFI_Acquisition` : les tests y réécrivent `.aefi_acquisition/configs/`, que git ne restaure pas. On vérifie ce qui part sur `main` dans une copie jetable, avant le push.
2. **Mise à jour du checkout réel.** Fermer l'application et le post-processeur avant. Après, comparer la casse des dossiers de `git ls-files` à celle du disque : Windows ne renomme pas un dossier dont seule la casse change, et Python échoue à l'import. Corriger par un renommage en deux temps.
3. **Tests localisés.** Lancer les tests des modules modifiés et de leurs importeurs directs ; la suite complète seulement avant `main`, quand l'écart est large. Cette ligne tient jusqu'à l'installation du standard des tests localisés.
4. **Parcours de l'opérateur.** Une fonction d'interface marche quand le clic atteint le service dans la composition de `main.py`, après `gc.collect()`. Un presenter est gardé vivant par un parent Qt, jamais par son service.
5. **Tranche testable d'abord.** Le premier livrable se lance au banc, puis un point, un commit, un retour de l'humain.
6. **Délégation suivie.** Un sous-agent fait au plus un commit ou un petit lot borné, puis rend compte. La session résume et attend l'accord avant le point suivant, et suit le `trace.log` du sous-agent en direct.
7. **Prompt d'un sous-agent.** Il nomme le mécanisme existant à réutiliser (`ExclusiveControl` / `take_all` pour l'exclusion, les actions de l'application comme « to-center » pour le mouvement) et les standards qui s'appliquent, même pour un outil de banc. « Minimal » borne le périmètre, jamais la structure.
8. **Pas d'automatisme caché.** Le labo change souvent de personnes : un état visible et une action que l'humain déclenche, avec confirmation.
9. **Un nom par concept.** Une seule clé par grandeur dans les configs, l'interface et le code, en unité physique. Un code de registre n'existe que dans l'adaptateur qui écrit le registre.
10. **Code présent n'est pas fonction validée.** Demander à l'humain avant de marquer une fonction matérielle comme faite dans `goals.md` ou `tasks.md`.
11. **Sigles développés.** Chaque sigle est développé à sa première occurrence : intention, commentaire, commit, réponse.
12. **Vue en direct au banc.** Un script qui pilote le matériel montre en direct sa phase, ses signaux, ses résultats et un bouton d'arrêt, jamais un journal seul.
13. **Sorties de caractérisation.** Elles vont dans `C:\Users\manip\Desktop\AEFI_Acquisition_Exports\HARDWARE-CHARACTERIZATION\` seulement. Rien n'est copié dans `0_inbox/data-a-interpreter/` du vault : l'humain décide. Un dossier temporaire créé dans le repo est retiré avant de rendre la main.
14. **Repos de thèse sur ce PC.** On travaille dans les clones de `C:\Users\manip\Desktop\THESE-LUIS-EXPERIMENTAL\`, poussés sur GitHub. Les repos Dropbox sont en lecture seule pour git, et le hook `refuser-git-dans-dropbox` le garantit. Si uv bute sur un lien Dropbox, `UV_LINK_MODE=copy`.
15. **Compte rendu de mesure.** Une phrase de verdict, un tableau court attendu contre mesuré, une ou deux phrases d'interprétation ; les branchements en petit tableau. Pas de tableaux empilés sans phrase entre eux.
