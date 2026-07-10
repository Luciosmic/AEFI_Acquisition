# position_2d — Intention

## Rationale

Value object représentant une position 2D dans l'espace de scan (x, y en mm). Type primitif du domain de scan — utilisé dans les trajectoires, les points de résultat et les commandes de motion.

## Responsibility

- Stocker `x: float` et `y: float` en millimètres.
- Servir de type commun pour `ScanTrajectory`, `ScanPointResult`, `IMotionPort.move_to()`.

## Design

- **`@dataclass(frozen=True)`** : immuable — une position ne change pas après création.
- Pas d'opérations vectorielles (celles-ci sont dans `Vector3D`) — simplicité voulue pour une coordonnée 2D plan.
