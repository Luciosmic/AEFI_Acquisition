---
type: point-de-composition::solidai-hexagonal
tldr: "Construire le service de traitement avec son lecteur de CSV et son écrivain d'étapes réels, sans fenêtre ni Qt."
code: ["[[external_modules/aefi_post_processor_module/interface/shell/headless_wiring.py]]"]
cause_de_changement: outil
cable: ["[[external_modules/aefi_post_processor_module/infrastructure/csv_scan_reader/csv_scan_reader_intention]]", "[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_writer/hdf5_step_writer_intention]]"]
---
# headless_wiring — Intention

## Rationale

Le traitement d'un scan se lance de deux endroits : l'acquisition, qui le calcule en fin de scan sans ouvrir de fenêtre, et la fenêtre du post-traitement. Si chaque appelant construit lui-même le lecteur et l'écrivain, les adaptateurs réels sont instanciés à plusieurs endroits et le service ne se câble pas sans Qt, ce que l'acquisition en processus léger n'a pas.

## Responsibility

- Construire `PostProcessingService` avec `CsvScanReader` et `Hdf5StepWriter` pour le fichier d'une acquisition.
- Rendre le service et son écrivain, que l'appelant ferme.

## Design

- Une fonction, aucun import de Qt : le raccord `ProcessingPipeline` et les tests de lancement l'appellent.
- C'est le seul module de `interface/` qui importe `infrastructure/` : les panneaux passent par les services.
