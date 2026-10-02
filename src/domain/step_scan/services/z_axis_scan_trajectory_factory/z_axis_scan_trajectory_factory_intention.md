# z_axis_scan_trajectory_factory — Intention

## Rationale

Sans ce service, l'échantillonnage des hauteurs (pas, convention point unique) serait recalculé par chaque consommateur, ce qui signifie qu'un opérateur guidé par l'UI et l'export pourraient ne pas parler des mêmes hauteurs, ce qui force à douter de chaque profil Z mesuré.

## Responsibility

- `create_trajectory(config: ZAxisScanConfig) -> ZAxisTrajectory` : `n_points` hauteurs équidistantes de `z_min_mm` à `z_max_mm`, croissantes.

## Design

- Factory stateless, symétrique de `LineScanTrajectoryFactory`.
- `n_points=1` : point unique à `z_min_mm` (début de plage), cohérent avec `ScanTrajectoryFactory`.
