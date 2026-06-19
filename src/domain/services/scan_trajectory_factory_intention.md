# scan_trajectory_factory — Intention

## Rationale

Encapsuler la génération des trajectoires de scan (serpentine, raster, comb) dans un service domain pur. La logique de path-planning est complexe, déterministe et réutilisable — elle appartient au domain, pas à l'infrastructure.

## Responsibility

- `create_trajectory(config: StepScanConfig) → ScanTrajectory` : calculer la liste ordonnée de `Position2D` selon le pattern et la zone de scan.
- Supporter les patterns SERPENTINE (boustrophedon), RASTER (gauche→droite systématique), COMB (colonne par colonne).

## Design

- **Factory stateless** (méthodes statiques) : pas d'état, facilement testable avec `pytest.mark.parametrize`.
- **Retourne `ScanTrajectory`** (value object) et non une liste brute : le type porte la sémantique et peut être itéré dans `StepScanExecutor`.
- Calcul des pas (`x_step`, `y_step`) avec gestion de la division par zéro (1 point → step = 0).
