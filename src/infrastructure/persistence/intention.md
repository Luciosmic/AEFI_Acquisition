# Persistence — Export et Stockage des Données

## Rationale
Ce module gère la persistance des données de scan et d'acquisition sur disque. Il exporte le scan en CSV, source brute unique (le post-traitement crée lui-même son HDF5 depuis ce CSV, depuis le 2026-11-19), en implémentant les ports définis par la couche application.

## Responsibility
- `CsvScanExportPort` (`csv_scan_export_port.py`) : implémenter `IScanExportPort`. Exporte les résultats de scan dans un fichier CSV lisible (une ligne par point de scan). Source brute unique de l'acquisition : le fichier des paramètres liste et hache ses fichiers, qui ne changent plus après l'export.

## Design
- Le répertoire de sortie par défaut est `.aefi_acquisition/scans/raw_data/` (gitignored, données runtime).
- `configure()` doit être appelé avant `write_point()` : ce contrat est documenté dans l'interface `IScanExportPort`.
