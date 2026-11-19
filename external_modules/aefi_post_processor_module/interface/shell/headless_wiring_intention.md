---
type: point-de-composition::solidai-hexagonal
tldr: "Construire les services de traitement, de catalogue et de carte avec leurs adaptateurs réels, sans fenêtre ni Qt."
code: ["[[external_modules/aefi_post_processor_module/interface/shell/headless_wiring.py]]"]
cause_de_changement: outil
cable: ["[[external_modules/aefi_post_processor_module/infrastructure/csv_scan_reader/csv_scan_reader_intention]]", "[[external_modules/aefi_post_processor_module/infrastructure/acquisition_parameters_scan_plan_reader/acquisition_parameters_scan_plan_reader_intention]]", "[[external_modules/aefi_post_processor_module/infrastructure/acquisition_provenance_reader/acquisition_provenance_reader_intention]]", "[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_writer/hdf5_step_writer_intention]]", "[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/export_folder_repository_intention]]", "[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_reader/hdf5_step_reader_intention]]"]
---
# headless_wiring — Intention

## Rationale

Le traitement d'un scan se lance de deux endroits : l'acquisition, qui le calcule en fin de scan sans ouvrir de fenêtre, et la fenêtre du post-traitement. Si chaque appelant construit lui-même le lecteur et l'écrivain, les adaptateurs réels sont instanciés à plusieurs endroits et le service ne se câble pas sans Qt, ce que l'acquisition en processus léger n'a pas.

## Responsibility

- Construire `PostProcessingService` avec `CsvScanReader`, `AcquisitionParametersScanPlanReader`, `AcquisitionProvenanceReader` et `Hdf5StepWriter` pour le fichier d'une acquisition, et rendre le service et son écrivain, que l'appelant ferme.
- Construire `AcquisitionCatalogService` (dépôt `ExportFolderRepository`) et `FieldMapService` (lecteur `Hdf5StepReader`).

## Design

- Une fonction par service, aucun import de Qt : le raccord `ProcessingPipeline` et les tests de lancement l'appellent.
- C'est le seul module de `interface/` qui importe `infrastructure/` : les panneaux passent par les services.
