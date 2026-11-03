# inertial_sensor_sample_acquired — Intention

## Rationale

Signaler qu'un nouvel échantillon du capteur inertiel est disponible. Sans cet
événement, le panneau d'affichage (et plus tard le détecteur de stabilité
mécanique) devrait interroger le port de flux, ce qui lierait le thread de
l'interface à une lecture bloquante.

## Responsibility

- Porter l'identifiant d'acquisition, l'index de l'échantillon, l'instant de
  réception (`timestamp_s`, secondes d'horloge monotone du PC) et les valeurs
  physiques des canaux présents :
  - `acceleration_g` : accélération, UCUM `[g]` ;
  - `angular_rate_dps` : vitesse angulaire, UCUM `deg/s` ;
  - `magnetic_field_ut` : champ magnétique, UCUM `uT` ;
  - `lidar_distance_mm` : distance lidar, UCUM `mm` (canal provisoire, non
    inertiel : voir dette).
- Chaque canal est `None` s'il n'est pas dans le flux.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, payload en primitives
  et tuples (pas de DTO d'application).
- Topic de publication : `"inertialsensorsampleacquired"`.
- Valeurs brutes converties uniquement : aucune calibration au repos (facteur
  issu d'une seule orientation).
- Dette `ponytail:` : `lidar_distance_mm` n'est pas une grandeur inertielle ;
  il est dans cet événement parce qu'il voyage dans le même flux.
