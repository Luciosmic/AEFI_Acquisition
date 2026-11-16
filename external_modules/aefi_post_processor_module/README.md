# Post-traitement AEFI

Module de l'acquisition qui calcule, à partir du CSV d'un scan, cinq étapes (`preprocessed`, `phase_calibrated`, `amplitude_subtracted`, `rotated_frame`, `interpolated`), les range dans le fichier `.h5` de l'acquisition et les montre dans une fenêtre à panneaux.
Même découpage en couches que `src/` : `domain/`, `application/`, `infrastructure/`, `interface/`. L'architecture est décrite dans `Data Processing Architecture.md`.

## Lancer la fenêtre

```bash
uv run python external_modules/aefi_post_processor_module/composition_root.py [options]
```

Le lancement ne calcule rien : la fenêtre s'ouvre sur la liste des acquisitions du dossier d'export, avec l'état de chacune (traitée, à recalculer, en échec), et le journal le dit (`acquisition.state`). Ouvrir la fenêtre ne modifie aucun fichier.
Le traitement part du bouton « Traiter » du panneau Acquisitions (la sélection, ou tout ce qui est à recalculer), ou au lancement avec `--force`.

| Option | Effet |
|---|---|
| `--repo-path <dossier>` | ouvre la fenêtre sur ce dossier d'export, au lieu de celui de la configuration d'export |
| `--force` | traite toutes les acquisitions avant d'afficher la fenêtre |
| `--log-file <fichier>` | fichier du journal de cette exécution (défaut : `.aefi_acquisition/logs/post_processor.log`) |
| `--layout-file <fichier>` | disposition des panneaux (défaut : `~/.aefi_post_processor_layout.dat`, jamais celle de l'acquisition) |

Les trois panneaux : Acquisitions (liste, état, bouton « Traiter », ouverture du dossier), Carte (tracé d'une étape d'une acquisition), Logs (journal).
Le bouton « Traiter » calcule sur le fil de la fenêtre : elle ne répond plus pendant le calcul.

## Ce que fait l'acquisition de son côté

Le service d'acquisition appelle le post-traitement à la fin d'un scan (`src/infrastructure/aefi_post_processor_port/`), puis ouvre la fenêtre avec `--repo-path`. Il passe par `processing/processing_pipeline.py`, un raccord temporaire qui garde l'ancienne signature.

## Vérifier

Depuis la racine du dépôt :

```bash
uv run pytest external_modules/aefi_post_processor_module -q                       # le module (deux échecs connus : 180° sur x et y)
~/.venvs/solidai-verify/bin/solidai verify --entry . --target external_modules/aefi_post_processor_module
```

`_tests/golden_master_test.py` rejoue le traitement sur trois scans synthétiques et compare chaque étape à `_tests/golden/` : il garde les chiffres identiques tant qu'on ne choisit pas de les changer.
Les scripts de `tool/` (validation analytique, campagnes synthétiques, exemple de pipeline) ne sont pas des tests.
