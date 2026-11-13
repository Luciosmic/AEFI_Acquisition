# Dettes D1 à D3 de la context map face au code (2026-10-10)

Bilan : aucune dette levée. D1 est à requalifier (son énoncé est faux), D2 est à planifier, D3 est à moitié préparée et à planifier.
Abréviations : `ACQ/`, `MCI/`, `FEM/` comme dans `etat-des-contrats.md`.

## D1 — `potentials_V` → `potential_sign` : non levée, et mal localisée

**Ce que dit la carte** : le champ vit dans le JSON d'Acquisition (`dgp.potentials_V`), il faut le renommer côté Acquisition.

**Ce que montre le code** :
- Acquisition n'écrit pas ce champ et ne l'a jamais écrit : `rg potentials_V ACQ/src` → 0, `git log --all -S'potentials_V'` → vide. L'export ne porte aucun potentiel par sphère, seulement `excitation.mode` et deux niveaux en pourcentage (`ACQ/src/application/scan/scan_export_service/scan_export_service.py:475-480`).
- Le consommateur FEM a déjà fait sa moitié : son modèle interne est `potential_sign: int` (`FEM/scripts/config/aefi_config.py:34`), et il lit encore `dgp["potentials_V"]` à l'entrée (`:67`, conversion `:84`).
- Dans MCI, `potentials_V` désigne selon l'endroit un signe ou une vraie tension : `±1` par défaut (`MCI/domain/aefi_device/value_objects/excitation_mode/excitation_mode.py:48`, `amplitude=1.0`), mais des volts dans `MCI/execute_pipeline_narda_primary_field_comparison.py:866` (`v * rms`) et `MCI/infrastructure/geometry_plotter/geometry_plotter.py:25,36` (« in volts »). Un renommage global en `potential_sign` y serait faux.
- Le seul producteur réel du triplet `positions_m / radii_m / potentials_V` est un export de métadonnées de MCI (`MCI/execute_pipeline_narda_primary_field_comparison.py:483-485`), pas Acquisition.

**Verdict** : à requalifier avant de planifier. La vraie dette est qu'aucun producteur n'émet le bloc que le FEM attend.

**Ce qu'il faudrait faire** (option la plus courte) : faire lire au FEM ce qu'Acquisition exporte déjà, `hardware_configuration.source_frame_reconstruction` (positions, rayons) et `excitation.mode` (dont se déduisent les signes par la table `EXCITATION_X_DIR_SIGNS`, `FEM/scripts/config/aefi_water_cylinder_scan_config.py:48`), puis supprimer la lecture de `potentials_V`. Point à trancher : l'export est en 2D, le FEM a besoin de z.
**Effort estimé** : une demi-journée (lecteur + tests `aefi_config_test.py`), hors décision sur z.

## D2 — Contrat `IForwardSolver` : non levée

**Preuve** : `rg 'IForwardSolver|eval_primary_field|eval_full_field|MCIAdapter|FEMAdapter'` → 0 occurrence dans le code. Les interfaces existantes sont sans rapport entre elles : `MCI/application/primary_field_service/i_api_primary_field_service.py:12-17` (grille, DTO xarray) et `FEM/scripts/fem/aefi_fem_solvers.py:20,76` (chemin de maillage, tuple Firedrake).

**Briques déjà là** : l'évaluation ponctuelle `(N,3) → (N,)` du primaire MCI existe côté FEM, `build_mci_charges` et `mci_potential` (`FEM/scripts/fem/aefi_mci_exact_bc.py:43-72`). C'est un `eval_primary_field` de fait.

**Ce qu'il faudrait faire** :
1. Décider où vit le port. Il n'y a pas de paquet commun : le FEM importe MCI par `sys.path` (`FEM/scripts/fem/aefi_mci_exact_bc.py:26-35`).
2. Écrire le port (`Protocol`), un `MCIAdapter` qui enveloppe les deux fonctions ci-dessus, un `FEMAdapter` qui enveloppe `fem_solve_primary` / `fem_solve_aefi` et l'évaluation ponctuelle Firedrake.
3. Trancher la grandeur de sortie : la carte dit le potentiel `u`, alors que les comparaisons à la mesure portent sur le champ E ou la tension différentielle du capteur.

**Effort estimé** : 1 à 2 jours, dont la moitié pour le point 1. Sans consommateur (le Post_Processor n'appelle aucun des deux), ce port n'a aujourd'hui qu'un client : les scripts de comparaison du repo FEM.

## D3 — `schema_version: "0.1-agile"` : non levée, à moitié préparée

**Ce que montre le code** :
- Le champ s'appelle `metadata_schema_version` et vaut `"0.3-agile"` pour les scans et séries temporelles (`ACQ/src/application/scan/scan_export_service/scan_export_service.py:467`). `0.1-agile` est la version de l'export du 2026-07-29 conservé dans le repo FEM.
- Un schéma 1.0 est spécifié (`ACQ/src/application/scan/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`) et sérialisé (`ACQ/src/infrastructure/persistence/acquisition_throughput/acquisition_parameters_v1_serializer.py:33-34,81`), mais il n'est branché que sur l'export de caractérisation de débit (`csv_acquisition_throughput_export_port.py:84`). Les scans restent en `0.3-agile`.
- Aucune validation nulle part : `rg 'jsonschema|pydantic'` → 0 dans Acquisition, MCI et FEM. Le lecteur FEM ne lit pas la version (`FEM/scripts/config/aefi_config.py:54-72`), il échoue sur `KeyError`.
- Le changement silencieux redouté a eu lieu deux fois depuis la carte : retrait de `aefi_device_hardware_identity` (2026-09-25), ajout de `source_frame_reconstruction` (2026-10-01). Aucun consommateur n'a cassé, parce qu'aucun ne lit l'export en production.

**Ce qu'il faudrait faire** :
1. Brancher le sérialiseur 1.0 sur l'export des scans (côté Acquisition).
2. Publier le schéma en fichier JSON Schema à côté du sérialiseur.
3. Valider la version à l'entrée de chaque consommateur, sur le modèle de `MCI/domain/aefi_device/aefi_device.py:156-160` qui refuse un `schema_version` inattendu.

**Effort estimé** : 1 à 2 jours pour le point 1 (selon l'écart entre le DTO du débit et celui du scan, non mesuré ici), une demi-journée pour 2 et 3.
