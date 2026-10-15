# adapter_inertial_sensor_stream_port — Intention

## Rationale

Le driver renvoie des entiers bruts par nom de capteur ; le port promet des
échantillons en unités physiques. Sans adaptateur, chaque consommateur
appliquerait lui-même la conversion, et deux conversions divergentes
afficheraient deux valeurs différentes pour la même ligne.

## Responsibility

- Implémenter `IInertialSensorStreamPort` au-dessus de `LSM9DS1StreamDriver` et
  de la conversion LSB vers unités physiques.
- Traduire les noms de canaux du port vers ceux du protocole (identiques).
- Transmettre la cadence demandée (`rate_hz`, optionnelle) au driver.

## Design

- **Aucune calibration au repos** : valeurs brutes converties uniquement (le
  facteur 0,9673 de la source vient d'une seule orientation).
- Le lidar traverse cet adaptateur comme canal du même flux (`lidar_raw`,
  `lidar_distance_mm`) : dette `ponytail:` du port.
- Port série et débit sont injectés par le constructeur (config JSON).
