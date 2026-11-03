# line_scan_trajectory_factory — Intention

## Rationale

Sans ce service, l'échantillonnage d'une ligne orientée (pas, convention point unique, ordre de parcours) serait recalculé par chaque consommateur — exécuteur, prévisualisation UI, export — ce qui signifie que deux lecteurs pourraient visiter des positions différentes pour la même config, ce qui force à comparer des mesures dont on ne sait plus où elles ont été prises.

## Responsibility

- `create_trajectory(config: LineScanConfig) -> ScanTrajectory` : `n_points` positions équidistantes de `s=-length/2` à `s=+length/2`.

## Design

- Factory stateless, retourne le `ScanTrajectory` existant tel quel (même consommateurs que la grille).
- `n_points=1` : point unique au **début** de la ligne (`s=-length/2`), cohérent avec le `step=0` de `ScanTrajectoryFactory` — pas le centre.
