# i_scan_export_port — Intention

## Rationale

Abstraire le format de persistence des résultats de scan (HDF5, CSV, JSON…) derrière un port. Le service d'export peut ainsi changer de format sans modifier la logique applicative.

## Responsibility

- Déclarer l'interface d'export des résultats de scan (méthode `export` ou équivalent).
- Servir de contrat entre `ScanExportService` et les adaptateurs de persistence.

## Design

- **Port outbound** placé dans `scan_application_service/` aux côtés du service consommateur.
- Implémenté par `HDF5ScanExportPort` et `CsvScanExportPort` dans `infrastructure/persistence/`.
