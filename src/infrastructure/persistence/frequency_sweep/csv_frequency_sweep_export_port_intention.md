---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `csv_frequency_sweep_export_port` : `open_export` : créer `<date>_frequencySweep_<rôle>_table<hauteur>mm/` sous le dossier d'export (Bureau, `AEFI_Acquisition_Exports`)."
code: ["[[src/infrastructure/persistence/frequency_sweep/csv_frequency_sweep_export_port.py]]"]
cause_de_changement: outil
implements: ["[[src/application/frequency_sweep/frequency_sweep_service/ports/i_frequency_sweep_export_port_intention]]"]
---
# csv_frequency_sweep_export_port — Intention

## Rationale

Les balayages seront relus pour être soustraits, comparés et combinés, d'abord par des scripts d'analyse : un CSV par fréquence se relit partout, et les échantillons bruts permettent de refaire la moyenne autrement.

## Responsibility

- `open_export` : créer `<date>_frequencySweep_<rôle>_table<hauteur>mm/` sous le dossier d'export (Bureau, `AEFI_Acquisition_Exports`).
- `export` : écrire `frequency_response.csv` (en-tête `# clé,valeur` : id du balayage, rôle, hauteur de table, statut ; puis une ligne par fréquence : rang, fréquence, N, décalage de phase de la référence, moyennes et écarts-types des 6 voies) et `samples.csv` (échantillons bruts, horodatage ISO 8601 avec décalage) ; retourner leur taille et leur SHA-256.
- `write_acquisition_parameters` : écrire `acquisition-parameters.json` (schéma 1.3) de façon atomique.

## Design

- Calque `CsvAcquisitionThroughputExportPort` (même dossier de base, mêmes fichiers communs : `acquisition_parameters_file`).
- Le rôle et la hauteur de table sont dans le nom du dossier pour l'œil humain seulement : la source est le contenu des fichiers.
- Erreur d'entrée/sortie → `OperationResult.fail`, journalisée.
