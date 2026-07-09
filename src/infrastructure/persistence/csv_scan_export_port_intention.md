# csv_scan_export_port — Intention

## Rationale

Implémentation CSV de `IScanExportPort` comme alternative légère au format HDF5 pour l'interopérabilité avec des outils tiers (Excel, MATLAB, Python basique). Le CSV est moins performant mais universellement lisible.

## Responsibility

- Exporter les résultats de scan 2D en CSV avec une ligne par point (position X, Y, et les 6 composantes de tension).
- Inclure un en-tête de colonnes.

## Design

- Implémente `IScanExportPort` — interchangeable avec `HDF5ScanExportPort` via injection.
- Utilise le module `csv` standard Python, sans dépendance externe.
