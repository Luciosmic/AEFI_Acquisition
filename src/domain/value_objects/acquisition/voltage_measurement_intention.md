# voltage_measurement — Intention

## Rationale

Value object fondamental de l'AEFI : représente une mesure de tension 6-canaux (X/Y/Z × In-Phase/Quadrature) acquise par l'ADS131A04. C'est la donnée élémentaire produite par le capteur à chaque position de scan.

## Responsibility

- Stocker les 6 composantes de tension en volts : `voltage_x_in_phase`, `voltage_x_quadrature`, `voltage_y_in_phase`, `voltage_y_quadrature`, `voltage_z_in_phase`, `voltage_z_quadrature`.
- Servir de type de retour pour `IAcquisitionPort.acquire_sample()` et de payload dans `ScanPointAcquired`.

## Design

- **`@dataclass(frozen=True)`** : immuable, hashable, comparable.
- Nommage explicite des composantes (pas de liste) : le code exprime la sémantique physique, pas juste 6 floats.
- Utilisé dans `MeasurementStatisticsService` pour l'averaging composante par composante.
