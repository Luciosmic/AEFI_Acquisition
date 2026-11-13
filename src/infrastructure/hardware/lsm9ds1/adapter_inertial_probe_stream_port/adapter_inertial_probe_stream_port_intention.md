---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `adapter_inertial_probe_stream_port` : Implémenter `IInertialProbeStreamPort` au-dessus de `LSM9DS1StreamDriver` et de la conversion LSB vers unités physiques."
code: ["[[src/infrastructure/hardware/lsm9ds1/adapter_inertial_probe_stream_port/adapter_inertial_probe_stream_port.py]]"]
cause_de_changement: outil
implements: ["[[src/application/inertial_probe/inertial_probe_service/ports/i_inertial_probe_stream_port_intention]]"]
---
# adapter_inertial_probe_stream_port — Intention

## Rationale

Le driver renvoie des entiers bruts par nom de capteur ; le port promet des
échantillons en unités physiques. Sans adaptateur, chaque consommateur
appliquerait lui-même la conversion, et deux conversions divergentes
afficheraient deux valeurs différentes pour la même ligne.

## Responsibility

- Implémenter `IInertialProbeStreamPort` au-dessus de `LSM9DS1StreamDriver` et
  de la conversion LSB vers unités physiques.
- Traduire les noms de canaux du port vers ceux du protocole (identiques).
- Transmettre la cadence demandée (`rate_hz`, optionnelle) au driver.

## Design

- **Aucune calibration au repos** : valeurs brutes converties uniquement (le
  facteur 0,9673 de la source vient d'une seule orientation).
- Le lidar traverse cet adaptateur comme canal du même flux (`lidar_distance`,
  construite ici par `LidarDistance.from_raw` : seul point de conversion du brut,
  0 = « pas de retour ») : dette `ponytail:` du port.
- Port série et débit sont injectés par le constructeur (config JSON).
