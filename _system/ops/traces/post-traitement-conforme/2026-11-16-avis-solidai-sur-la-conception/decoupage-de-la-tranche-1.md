---
doc_type: avis-solidai
type: constat::sh-agent-os
genere_par: "[[tache - avis solidai sur la conception]]"
---

# Découpage de la tranche 1 (conformité de base)

Dix étapes, dont neuf commits. Chaque commit laisse les tests au vert (sauf les deux échecs connus, inchangés jusqu'à la tranche 5) et se vérifie seul.
Décisions de fond : voir `avis-sur-les-trois-points-a-trancher.md` ; corrections de structure : voir `ecarts-de-la-conception-aux-standards-solidai.md` (numéros « E » ci-dessous).

## Worktree et périmètre

- **Worktree requis** : `git worktree add "../AEFI_Acquisition_dev_post_processor" -b dev_post_processor develop` (CLAUDE.md : contexte borné `dev_<contexte>`). Lire `VENV.md` avant de créer l'environnement du worktree.
- **Le périmètre « module seul » tient** pour toute la tranche 1, à deux conditions que la conception ne posait pas : garder le nom `composition_root.py` (E1) et garder le raccord `processing/processing_pipeline.py` (E6). Sans elles, l'adaptateur, le panneau « External Modules » et le lanceur `.bat` de `src/` et de `launch/` casseraient.
- Aucun fichier de `src/` ni de `launch/` ne change en tranche 1. La tranche 6 sort du worktree : branche `feature/*` depuis `develop`, après la fusion de `dev_post_processor`.

## Commandes d'acceptation de référence

Depuis la racine du worktree (`uv run`), notées `V` dans les tests ci-dessous :
- `V1` : `uv run pytest external_modules/aefi_post_processor_module -q`
- `V2` : `~/.venvs/solidai-verify/bin/solidai verify --entry . --target external_modules/aefi_post_processor_module`
- `V3` (le côté acquisition, ne change pas) : `uv run pytest src/infrastructure/aefi_post_processor_port src/application/scan/scan_application_service/_tests/scan_export_with_post_processing_integration_test.py src/interface/widgets/panels/_tests/external_modules_panel_test.py`

Base mesurée à `develop` (efa1c540) : `V1` = 8 réussis, 2 échecs (`amplitude_subtraction_test::test_offset_removal`, `phase_calibration_test::test_phase_recovery`, écart de 180° sur x et y, `extract_border_pixels` absent) ; `V2` = 1 erreur (intention du journal sans type). `V3` : à relever en 1.0.

## 1.0 — Préparation (pas de commit de code)

Créer le worktree ; relever `V1`, `V2`, `V3` ; écrire les résultats dans la trace de la tâche.
**Test d'acceptation :** les trois relevés sont dans la trace, `git worktree list` montre `dev_post_processor`.

## 1.1 — Étalon de non-régression

Avant tout déplacement : exécuter le traitement actuel (`ProcessingPipeline`) sur trois CSV de `_tests/synthetic_scans_data_repository/batch_20260123_201635/` (`scan_001_baseline`, `scan_004_rotation_z45`, et un scan incomplet rempli de NaN, à générer par `synthetic_scan_generator` si aucun ne l'est) et enregistrer chaque étape en `.npz` et ses métadonnées en `.json` dans `_tests/golden/` (jamais `.h5`, ignoré par git). Ajouter `golden_master_test.py`, qui rejoue le traitement par le nom public `ProcessingPipeline` et compare chaque étape (`np.array_equal`, `equal_nan=True`) et chaque métadonnée.
**Test d'acceptation :** le test passe sur le code inchangé ; en changeant temporairement `interpolation_method` de `'cubic'` à `'linear'` dans `ProcessingPipeline`, il échoue (preuve qu'il voit une dérive), puis on annule. Ne pas prendre `border_width` : `PrimaryFieldPhaseCalibrator` et `PrimaryFieldAmplitudeSubtractor` le stockent sans le lire, le changer ne dérive rien. Il fait 15 comparaisons de tableaux (5 étapes par scan, 3 scans). Il restera tel quel jusqu'à la tranche 6.

## 1.2 — Rangement hors des couches

- Les scripts du `_tests/` vont dans `tool/` (E14) : `debug_imports`, `inspect_baseline_values`, `reproduce_phase_bug`, `verify_theta_noise`, `run_analytic_validation`, `run_synthetic_campaign`, `generate_synthetic_campaign`, plus `example_pipeline.py`. Leurs imports sont mis à jour.
- Typer `logging_setup_intention.md` (`atome`, cause `outil`) et la ranger tout de suite sous `infrastructure/logging/` avec `logging_setup.py` : A15 refuse la cause `outil` hors de `infrastructure/` ou `interface/`, donc le typer sur place laisse une erreur. A1 exige alors un `_tests/` : les deux tests du journal quittent `observability_test.py` pour `infrastructure/logging/_tests/`. Fait en 1.2.
- Aligner `numpy~=2.2` et `scipy~=1.14` dans `pyproject.toml` du module (E3).
**Test d'acceptation :** `V1` identique à la base (8 réussis, 2 échecs, mêmes noms) ; `V2` = 0 erreur ; le test d'étalon 1.1 passe ; chaque script de `tool/` s'importe sans erreur (`uv run python -c "import runpy; runpy.run_path('<script>', run_name='check')"`).

## 1.3 — Le domaine

Règle trouvée à l'exécution : les imports internes du domaine (code et `_tests/`) sont relatifs, jamais qualifiés par `aefi_post_processor_module.` : A9 compte un import qualifié comme extérieur au domaine. Les générateurs de tests partagés n'importent pas pandas (`to_rows` au lieu de `to_dataframe`).

Créer `domain/processing/` (E8) : un dossier par atome, chacun avec son `<nom>_intention.md` typé `atome` (cause `regle-metier`), son code et son `_tests/` : `grid_builder` (le cœur numpy de `DataPreProcessor.create_square_grid`, sans pandas), `phase_calibrator`, `amplitude_subtractor`, `frame_rotator`, `interpolator`, `processing_steps` (noms et ordre fermés : `preprocessed`, `phase_calibrated`, `amplitude_subtracted`, `rotated_frame`, `interpolated` ; paramètres gelés : largeur du bord, méthode d'interpolation, taille de grille, point de référence, angles). Les tests de calcul existants (`phase_calibration_test`, `amplitude_subtraction_test`, `frame_rotation_test`, `interpolation_test`) suivent leur atome. Les anciens fichiers `processing/primary_field_*`, `sensor_to_ef_*`, `data_interpolator.py` sont supprimés ; `processing_pipeline.py`, `data_preprocessor.py` (partie pandas, qui appelle `grid_builder`) et `datahandler.py` restent pour l'instant et importent le domaine. Créer `_tests/architecture_test.py` (domaine et application n'importent ni `PySide6`, ni `pandas`, ni `h5py`, ni `pathlib`, ni `aefi_acquisition_upstream`, ni `interface`/`src` ; aucun import non qualifié `from domain…`).
**Test d'acceptation :** `golden_master_test` passe sans écart (preuve que les chiffres n'ont pas bougé) ; `V1` = 8 réussis et les 2 mêmes échecs (messages identiques : 180° sur x et y) ; `V2` = 0 erreur ; `architecture_test` passe ; l'intention de chaque atome a ses trois titres (A3).

## 1.4 — Le service de traitement, son lecteur de CSV et son écrivain d'étapes

- `application/post_processing_service/` : intention, `i_api_post_processing_service.py`, `dtos/` (gelés, H8), `post_processing_service.py`, `ports/` (`i_csv_scan_reader.py`, `i_step_writer.py`), `_tests/`. Le service enchaîne les cinq étapes comme `ProcessingPipeline.run_full_pipeline` et rend le même résumé (`steps_completed`, `errors`, `processing_history`).
- `infrastructure/aefi_export/csv_scan_reader/` (pandas, rend des tableaux numpy) et `infrastructure/persistence/hdf5/step_writer/` (la partie écriture de `DataHandler`, h5py), avec chacun son intention, son `fake/` et sa suite de contrat (écrire puis relire rend les mêmes valeurs ; l'échec d'un fichier absent est le même que le vrai). Le chemin du fichier d'étapes sort de `processing_store_path()` (point 1).
- Câblage sans Qt : `interface/shell/headless_wiring.py` (`point-de-composition`).
- `processing/processing_pipeline.py` devient le raccord (E6) : même signature, délègue au service par le câblage sans Qt, marqué `# ponytail:` (retrait en tranche 6). `data_preprocessor.py` et la partie écriture de `datahandler.py` sont supprimés.
**Test d'acceptation :** `golden_master_test` inchangé et vert ; **`V3` vert** (le test d'intégration de l'acquisition produit toujours un seul `.h5` avec les cinq étapes, et `aefi_post_processor_port_test` voit encore le nom patché) ; `V1` identique à la base ; `V2` = 0 erreur (H7, H8, H9, H10, H16, H18, H20 comprises) ; `architecture_test` vert.

## 1.5 — Le catalogue des acquisitions et la lecture d'une carte

- `domain/acquisition_record/` : la racine `AcquisitionRecord` avec la règle « à recalculer » (E7), `repositories/i_acquisition_repository.py`, intention, `_tests/`. Le domaine désigne les dossiers par des chaînes (E3).
- `application/acquisition_catalog_service/` (liste les acquisitions avec leur état : traitée, à recalculer, en échec ; l'échec garde son message pour la session) et `application/field_map_service/` (liste les étapes d'une acquisition, charge une étape en DTO) ; ports `i_step_reader.py` pour la carte.
- `infrastructure/aefi_export/export_folder_repository/` (le parcours `<horodatage>_<stepScan|flyScan>_<nom>/*_aefi.csv` de `sync_scans`, et les dates des fichiers) et `infrastructure/persistence/hdf5/step_reader/` (la lecture de `DataHandler` et de `VisualisationModel`), chacun avec son `fake/`, sa suite de contrat et ses intentions.
**Test d'acceptation :** sur un dossier temporaire construit avec les CSV synthétiques, le catalogue rend « à recalculer » (CSV sans fichier d'étapes), « traitée » (après traitement par le service), « à recalculer » de nouveau (CSV retouché plus tard), « en échec » avec son message (CSV tronqué) ; il ne crée ni ne modifie aucun fichier (liste des fichiers et des dates identique avant et après) ; la carte d'une étape traitée rend les mêmes tableaux et les mêmes bornes que `VisualisationModel.get_step_data` sur le même fichier (comparaison directe avec l'ancien modèle encore présent) ; `V1` et `V2` comme avant ; `V3` vert.

## 1.6 — La coquille : emprunt, fenêtre à panneaux, journal

- `aefi_acquisition_upstream/` : `__init__.py` (le raccord de `sys.path`, point 3), intention `atome` (outil) qui liste les objets empruntés, leur source et pourquoi ; re-exports de `WindowsCarrier`, `CarrierPresentationModel`, `ModernTaskbar`, `TaskbarPresenter`, `TaskbarPresentationModel`.
- `interface/shell/` : fenêtre avec le conteneur de panneaux et la barre de tâches (sur le modèle de `src/interface/shell/dashboard.py`), disposition enregistrée dans un fichier propre au post-traitement (jamais `~/.aefi_acquisition_layout.dat`).
- `infrastructure/logging/` tient déjà `logging_setup.py` et son intention (fait en 1.2) ; panneau Logs et son presenter (`logs_presenter`, typé), ouverture du fichier journal (récit R17).
- `composition_root.py` reste le point d'entrée mince ; la fenêtre ouverte est la nouvelle, avec les panneaux Logs seulement ; l'ancienne fenêtre `visualisation/` reste le chemin par défaut jusqu'en 1.7.
**Test d'acceptation :** test de lancement en sous-processus, `QT_QPA_PLATFORM=offscreen uv run python external_modules/aefi_post_processor_module/composition_root.py --repo-path <dossier temporaire>`, qui attend la ligne `window.shown` dans le fichier journal puis termine le processus (c'est lui qui prouve que `import interface` résout bien vers `src/`, E5) ; test d'un presenter avec Fakes (ouverture du journal) ; `architecture_test` vert ; `V1`, `V2`, `V3` comme avant ; l'application d'acquisition et le panneau « External Modules » lancent toujours `composition_root.py` (test `external_modules_panel_test`).

## 1.7 — Panneaux Acquisitions et Carte, retrait de l'ancienne fenêtre

- Panneau Acquisitions (liste, type, objet à lire dans le nom du dossier tant que la tranche 2 n'est pas faite, état, bouton « Traiter » pour la sélection ou pour tout ce qui est à recalculer, ouverture du dossier : R1, R2, R17) et son presenter ; panneau Carte (tracé de `FigureFactory`, choix de l'étape comme dans l'ancienne vue) et son presenter ; les deux panneaux sont des vues humbles, sans type ni logique (E9). Le bilan du traitement (traités, à jour, en échec, avec l'étape fautive) s'écrit dans Logs.
- Suppression de `visualisation/`, de `composition_root_visualisation.py` et de la logique de `sync_scans` dans `composition_root.py`. Le traitement au lancement reste, appelé par le service (comportement inchangé jusqu'en 1.8).
**Test d'acceptation :** test d'un presenter avec Fakes : sélectionner une acquisition charge la carte de l'étape choisie, le bouton « Traiter » appelle le service une fois par acquisition à recalculer et produit les cinq étapes (relues par le lecteur) ; l'échec d'une acquisition ne stoppe pas les suivantes et se lit dans le bilan ; test en sous-processus 1.6 reprend, avec la liste affichée d'au moins une acquisition ; `golden_master_test`, `V1` (les dix tests d'origine, deux échecs connus), `V2`, `V3` verts comme avant ; `rg -n "visualisation" external_modules/aefi_post_processor_module -g '*.py'` ne renvoie plus rien.

## 1.8 — Le lancement ne calcule plus (point 2)

`composition_root.py` n'appelle plus le traitement ; `--force` reste et signifie « traiter tout au lancement » ; `--repo-path` reste. Le statut de chaque acquisition s'affiche à l'ouverture.
**Test d'acceptation :** test en sous-processus sur un dossier temporaire qui contient une acquisition sans fichier d'étapes : après lancement puis arrêt, la liste des fichiers et leurs dates sont identiques à l'avant et le journal contient l'état « à recalculer » ; avec `--force`, les cinq étapes existent ; `V3` vert (l'adaptateur continue de calculer lui-même puis ouvre la fenêtre sur le dossier).

## 1.9 — Documents, vérification d'ensemble, fusion

Mettre à jour `README.md`, `Data Processing Architecture.md`, `processing/README.md` (qui ne garde que le raccord), les diagrammes ; mettre à jour le plan (« Prochaine action » : tranche 2) ; passer `V1`, `V2`, `V3` puis `solidai verify --entry . --target .` à la racine du worktree et le comparer à `develop` (aucune erreur nouvelle) ; fusionner `dev_post_processor` dans `develop` (`--no-ff`, message `[quoi] — [pourquoi]`).
**Test d'acceptation :** les quatre commandes ci-dessus sont dans la trace, avec `V1` à 2 échecs connus et rien d'autre ; l'humain lance `composition_root.py` sur ses vraies acquisitions et voit la liste, sans qu'aucun fichier ne change à l'ouverture, et traite une acquisition par le bouton.
