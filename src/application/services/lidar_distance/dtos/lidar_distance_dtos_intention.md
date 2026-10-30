# lidar_distance_dtos — Intention

> Extrait des DTO de la calibration par barre (abandonnée le 2026-10-30) : seul
> `LidarDistanceReading`, la sortie du port LIDAR, est repris ici.

## Rationale

Sans DTO, le port LIDAR rendrait un tuple dont le sens (secondes ? millimètres ?
heure de réception ou de lecture ?) ne serait porté que par la position.

## Responsibility

- `LidarDistanceReading` : une distance horodatée à sa réception (sortie du port LIDAR).

## Design

- `@dataclass(frozen=True)` ; unités dans les noms de champs et dans l'en-tête du
  module (mm, s).
