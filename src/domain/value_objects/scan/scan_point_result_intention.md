# scan_point_result — Intention

## Rationale

Value object encapsulant le résultat d'acquisition en un point de scan : position 2D + mesure de tension + index. Bundler ces trois informations dans un type immuable garantit la cohérence des données et facilite le passage à `ScanPointAcquired` event.

## Responsibility

- Stocker `position: Position2D`, `measurement: VoltageMeasurement`, `point_index: int`.
- Servir d'unité de donnée entre `StepScanExecutor` et l'agrégat `StepScan`.

## Design

- **`@dataclass(frozen=True)`** : immuable après création.
- Pas de logique de calcul — pure structure de données.
