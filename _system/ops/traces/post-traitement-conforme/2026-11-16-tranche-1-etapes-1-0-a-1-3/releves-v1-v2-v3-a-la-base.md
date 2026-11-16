---
doc_type: releve
type: constat::sh-agent-os
genere_par: "[[tache - tranche 1 etapes 1 0 a 1 3]]"
---

# Relevés V1, V2, V3 à la base (develop efa1c540, worktree dev_post_processor)

Étape 1.0. Commandes lancées depuis `AEFI_Acquisition_dev_post_processor/`, avec `UV_PROJECT_ENVIRONMENT=~/.venvs/AEFI_Acquisition_dev_post_processor` (venv propre au worktree, créé par `uv sync --extra dev`, hors Dropbox : voir `VENV.md`).

| Relevé | Commande | Résultat | Log brut |
|---|---|---|---|
| V1 | `uv run pytest external_modules/aefi_post_processor_module -q` | 8 réussis, 2 échecs : `amplitude_subtraction_test::test_offset_removal`, `phase_calibration_test::test_phase_recovery` (x : attendu 10°, obtenu -170° ; y : attendu -25°, obtenu 155° ; `extract_border_pixels` absent) | `pytest-v1-a-la-base.log` |
| V2 | `~/.venvs/solidai-verify/bin/solidai verify --entry . --target external_modules/aefi_post_processor_module` | 1 erreur : `solidai-intention-non-typee` sur `logging_setup_intention.md` ; 46 contrôles joués | `solidai-verify-v2-a-la-base.log` |
| V3 | `QT_QPA_PLATFORM=offscreen uv run pytest src/infrastructure/aefi_post_processor_port src/application/scan/scan_application_service/_tests/scan_export_with_post_processing_integration_test.py src/interface/widgets/panels/_tests/external_modules_panel_test.py -q` | 8 réussis, 0 échec | `pytest-v3-a-la-base.log` |

`git worktree list` montre `dev_post_processor` à efa1c540, arbre propre.

Note V2 : le démon au-engine du worktree n'était pas lancé ; il a été démarré par `sh-agent-os/scripts/demarrer-les-demons-d-un-vault.sh` (la commande `au daemon start` directe a été tuée à 120 s).
