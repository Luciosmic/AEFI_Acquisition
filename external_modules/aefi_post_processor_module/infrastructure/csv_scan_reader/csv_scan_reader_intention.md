---
type: adaptateur::solidai-hexagonal
tldr: "Lire un CSV de scan avec pandas et rendre des tableaux numpy."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/csv_scan_reader/csv_scan_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-csv-scan-reader]]"]
---
# csv_scan_reader — Intention

## Rationale

Le CSV d'un scan est le format d'export de l'acquisition. Sans lecteur dédié, pandas entre dans le service ou le domaine, qui ne peuvent plus se tester sans fichier.

## Responsibility

- Implémenter `ICsvScanReader` : refuser un fichier absent, rendre avec les points le SHA-256 des octets lus (le même fichier que celui dont l'acquisition a consigné l'empreinte), garder les colonnes de tension présentes dans l'ordre x, y, z, en phase puis en quadrature.

## Design

- Une classe, pandas pour lire, numpy pour rendre ; la même suite de contrat que son Fake.
