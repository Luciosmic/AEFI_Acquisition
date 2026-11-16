---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure du lecteur de grille prévue : des grilles en mémoire par CSV, rien pour un scan non décrit, comme le réel."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/acquisition_parameters_scan_plan_reader/fake/fake_acquisition_parameters_scan_plan_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-scan-plan-reader]]"]
double_de: "[[external_modules/aefi_post_processor_module/infrastructure/acquisition_parameters_scan_plan_reader/acquisition_parameters_scan_plan_reader_intention]]"
---
# fake_acquisition_parameters_scan_plan_reader — Intention

## Rationale

Le lecteur réel exige un fichier des paramètres sur disque. Sans double en mémoire, chaque test du service devrait écrire ce fichier.

## Responsibility

- Garder des grilles prévues en mémoire, par chemin de CSV, et ne rien rendre pour un scan non décrit, comme le réel.

## Design

- Passe la suite de contrat de `IScanPlanReader`, comme l'adaptateur réel.
