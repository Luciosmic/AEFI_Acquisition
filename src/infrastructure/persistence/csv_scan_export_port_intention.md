---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `csv_scan_export_port` : Exporter les résultats de scan 2D en CSV avec une ligne par point (position X, Y, et les 6 composantes de tension)."
code: ["[[src/infrastructure/persistence/csv_scan_export_port.py]]"]
cause_de_changement: outil
implements: ["[[src/application/scan/scan_export_service/ports/i_scan_export_port_intention]]"]
---
# csv_scan_export_port — Intention

## Rationale

Implémentation CSV de `IScanExportPort` comme alternative légère au format HDF5 pour l'interopérabilité avec des outils tiers (Excel, MATLAB, Python basique). Le CSV est moins performant mais universellement lisible.

## Responsibility

- Exporter les résultats de scan 2D en CSV avec une ligne par point (position X, Y, et les 6 composantes de tension).
- Inclure un en-tête de colonnes.
- À l'arrêt, remplacer le journal du scan (`_logs.log`) et le flux de l'accéléromètre (`_accelerometer.csv`) par une archive `.xz` chacun, avant le document des paramètres qui liste et hache ce qui est dans le dossier. Un échec de compression garde le fichier en clair. N'écrire aucun fichier d'événements.

## Design

- Implémente `IScanExportPort` — interchangeable avec `HDF5ScanExportPort` via injection.
- Utilise le module `csv` standard Python, sans dépendance externe.
