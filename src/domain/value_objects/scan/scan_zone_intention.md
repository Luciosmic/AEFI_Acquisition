# scan_zone — Intention

## Rationale

Value object définissant la région rectangulaire 2D à scanner (x_min, x_max, y_min, y_max en mm). Encapsuler la zone dans un type dédié permet la validation des bornes et rend la sémantique explicite dans `StepScanConfig`.

## Responsibility

- Stocker les bornes de la zone de scan.
- Valider : x_min < x_max, y_min < y_max.
- Calculer la largeur et hauteur de la zone si nécessaire.

## Design

- **`@dataclass(frozen=True)`** avec validation dans `__post_init__`.
- Utilisé dans `StepScanConfig`, `ScanTrajectoryFactory`, et exposé dans `ScanStarted` event.
