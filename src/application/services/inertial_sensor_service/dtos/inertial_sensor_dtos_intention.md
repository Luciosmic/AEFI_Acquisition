# inertial_sensor_dtos — Intention

## Rationale

Sans DTO gelé pour un échantillon de capteur inertiel, le port de flux
renverrait des tuples anonymes ou des dictionnaires : l'accélération en g et
le champ magnétique en µT deviendraient indiscernables au site d'appel, et
chaque consommateur (exécuteur, presenter) réinventerait sa lecture. Le DTO
fixe le nom, l'unité et l'optionalité de chaque canal à la frontière du port.

## Responsibility

- `InertialSensorStreamSample` : une ligne du flux, horodatée à la réception
  sur le PC (secondes, `perf_counter`). Chaque canal est optionnel : le flux
  peut n'en porter qu'un sous-ensemble.
  - `acceleration_g` : accélération, en g (UCUM `[g]`).
  - `angular_rate_dps` : vitesse angulaire, en °/s (UCUM `deg/s`).
  - `magnetic_field_ut` : champ magnétique, en µT (UCUM `uT`).
  - `lidar_raw`, `lidar_distance_mm` : canal lidar, voir dette ci-dessous.
- `InertialSensorAcquisitionConfig` : canaux demandés pour une acquisition.
- Constantes de noms de canaux (`ACCELEROMETER_CHANNEL`, ...).

## Design

- `@dataclass(frozen=True)`, valeurs en primitives et tuples.
- **Dette non silencieuse** : le lidar mesure une distance, ce n'est pas un
  capteur inertiel. Il est ici un canal du même flux (`lidar_*`) parce qu'il
  est sur la même carte et la même liaison série, ce qui est une considération
  d'infrastructure, pas de domaine. À terme : concept et port lidar séparés
  (voir `_system/ops/ponytail-debt.md`).
