# z_axis_trajectory — Intention

## Rationale

Sans ce module, un scan Z devrait se loger dans `ScanTrajectory`, qui ne porte que des `Position2D` : la hauteur disparaîtrait de la consigne, ce qui signifie que N points identiques en XY seraient indiscernables, ce qui force l'exécuteur et l'export à reconstruire Z par un index implicite.

## Responsibility

- Porter la consigne ordonnée d'un scan Z : position XY fixe + liste ordonnée des hauteurs à visiter.

## Design

- `@dataclass(frozen=True)`, mêmes ergonomies que `ScanTrajectory` (`__iter__`, `__len__`, `__getitem__`, `total_points`) — l'itération porte sur les hauteurs `z`.
- Pas de `Position3D` : XY est constant par définition, une seule valeur suffit (YAGNI tant qu'un scan 3D n'existe pas).
