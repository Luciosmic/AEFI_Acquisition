# aefi_voltage_measurement — Intention

## Rationale

Value object fondamental de l'AEFI : représente une mesure de tension 6-canaux (X/Y/Z × In-Phase/Quadrature) acquise par l'ADS131A04, en phase avec l'excitation DDS (AD9106). C'est la donnée élémentaire produite par le capteur AEFI à chaque position de scan — nommée explicitement `Aefi` car ce n'est pas une tension générique : c'est la détection synchrone propre à la technique de fluorescence d'impédance, à distinguer de `FieldMeasurement` (sonde Narda EP-601, amplitude seule, sans référence de phase).

## Responsibility

- Stocker les 6 composantes de tension en volts : `voltage_x_in_phase`, `voltage_x_quadrature`, `voltage_y_in_phase`, `voltage_y_quadrature`, `voltage_z_in_phase`, `voltage_z_quadrature`.
- Servir de type de retour pour `IAcquisitionPort.acquire_sample()` et de payload dans `ScanPointAcquired`.

## Design

- **`@dataclass(frozen=True)`** : immuable, hashable, comparable.
- Nommage explicite des composantes (pas de liste) : le code exprime la sémantique physique, pas juste 6 floats.
- Utilisé dans `MeasurementStatisticsService` pour l'averaging composante par composante.
