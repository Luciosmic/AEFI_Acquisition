---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure du lecteur de CSV : des scans en mémoire, refus d'un chemin absent identique au réel."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/csv_scan_reader/fake/fake_csv_scan_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-csv-scan-reader]]"]
double_de: "[[external_modules/aefi_post_processor_module/infrastructure/csv_scan_reader/csv_scan_reader_intention]]"
---
# fake_csv_scan_reader — Intention

## Rationale

Le lecteur réel exige un fichier sur disque. Sans double en mémoire, chaque test du service devrait écrire un CSV.

## Responsibility

- Garder des scans en mémoire, par chemin, et refuser un chemin inconnu comme le réel.

## Design

- Passe la suite de contrat de `ICsvScanReader`, comme l'adaptateur réel.
