---
doc_type: constat
type: constat::sh-agent-os
genere_par: "[[tache - tranche 1 etapes 1 0 a 1 3]]"
---

# Étape 1.4 : adaptateurs à plat, raccord réduit

## Adaptateurs à plat sous `infrastructure/`

Le découpage place `csv_scan_reader` sous `infrastructure/aefi_export/` et `step_writer` sous `infrastructure/persistence/hdf5/`.
H16 (`solidai-adaptateur-mal-place`) n'admet un dossier de regroupement que pour `hardware/` : un adaptateur est `infrastructure/<adaptateur>/<adaptateur>.py`.
Sous `aefi_export/`, la vérification demanderait `aefi_export/aefi_export.py`. La demande de regroupement `persistence/` est déjà ouverte côté `src/` (trace `adaptateurs-de-persistance-et-d-execution-a-discuter`).

Décision : dossiers à plat, nommés d'après leur contenu, valables pour 1.5 aussi.
- `infrastructure/csv_scan_reader/` (+ `fake/`)
- `infrastructure/hdf5_step_writer/` (+ `fake/`)
- `infrastructure/hdf5_step_format/` : constantes de format et `processing_store_path()`, partagées par l'écrivain (1.4) et le lecteur d'étapes (1.5). Atome `outil` avec ses tests.
- En 1.5 : `infrastructure/hdf5_step_reader/` et `infrastructure/export_folder_repository/`.

## Raccord `processing/processing_pipeline.py`

Garde `ProcessingPipeline(output_path, border_width, interpolation_method, target_grid_size)`, `run_full_pipeline(csv_path, rotation_angles, reference_point, skip_interpolation)`, `close()` et le gestionnaire de contexte, et rend le même dictionnaire.
Perdu, sans appelant hors du module : `run_partial_pipeline`, `get_current_data`, `current_data`.
`data_handler` reste un attribut (c'est l'écrivain d'étapes) : `golden_master_test`, inchangé, appelle `pipeline.data_handler.close()`.
`DataHandler` ne garde que la lecture (`visualisation/model.py` s'en sert jusqu'en 1.5/1.7).

## Contrats

Suites de contrat dans `_tests/` de l'adaptateur réel (`csv_scan_reader_contract.py`, `hdf5_step_writer_contract.py`), importées par les tests du Fake : H20 repère le motif « contract » dans la cible d'import.
Le port `IStepWriter` porte `load_step` pour que « écrire puis relire rend les mêmes valeurs » se vérifie par le port.

## Ports

Enregistrements `^:` dans le champ `ports` de l'intention du service (un fichier d'intention de port à part laisse A20 sans type : `port` n'est pas un sous-type d'atome). Les adaptateurs les visent par `[[intention^^id]]`.
