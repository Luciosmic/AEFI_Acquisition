# scan_pattern — Intention

## Rationale

Enum domain définissant les stratégies de trajectoire de scan. Centraliser les patterns dans un type énuméré empêche les chaînes magiques et rend les branches dans `ScanTrajectoryFactory` exhaustives et vérifiables statiquement.

## Responsibility

- Définir SERPENTINE (boustrophedon), RASTER (gauche→droite), COMB (colonne par colonne).
- Être utilisé comme discriminant dans `ScanTrajectoryFactory.create_trajectory()`.

## Design

- **`enum.Enum`** Python standard.
- Référencé dans `StepScanConfig`, `Scan2DConfigDTO` (via `ScanPattern[dto.scan_pattern]`).
