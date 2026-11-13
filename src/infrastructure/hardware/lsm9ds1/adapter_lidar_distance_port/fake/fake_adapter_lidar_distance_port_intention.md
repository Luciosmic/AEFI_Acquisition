---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_adapter_lidar_distance_port` : Implémenter `ILidarDistancePort` : une distance toutes les 40 ms (25 Hz mesurés sur la carte) de l'horloge injectée, valeur donnée par une fonction (scène de barre lisant un faux moteur), horodatée à son instant d'arrivée."
code: ["[[src/infrastructure/hardware/lsm9ds1/adapter_lidar_distance_port/fake/fake_adapter_lidar_distance_port.py]]"]
cause_de_changement: outil
implements: ["[[src/application/inertial_probe/lidar_distance/ports/i_lidar_distance_port_intention]]"]
double_de: "[[src/infrastructure/hardware/lsm9ds1/adapter_lidar_distance_port/adapter_lidar_distance_port_intention]]"
---
# fake_adapter_lidar_distance_port — Intention

## Rationale

Le service de calibration doit être testé sans carte ni LIDAR, et en accéléré. Un
LIDAR qui répondrait instantanément cacherait l'essentiel : pendant le fly scan, une
distance n'arrive que toutes les 40 ms et le moteur avance entre deux ; à l'arrêt,
les distances arrivées pendant la stabilisation doivent être écartées.

## Responsibility

- Implémenter `ILidarDistancePort` : une distance toutes les 40 ms (25 Hz mesurés sur
  la carte) de l'horloge injectée, valeur donnée par une fonction (scène de barre
  lisant un faux moteur), horodatée à son instant d'arrivée.
- Reproduire les défaillances du réel : flux déjà diffusé par le panneau
  (`LidarStreamBusyError`), ouverture impossible, flux muet après n échantillons,
  et les « pas de retour » (le LIDAR réel envoie 0 quand il ne mesure rien,
  premier essai au banc 2026-10-15) : la scène renvoie None là où rien ne revient
  (sol hors de portée), et une proportion paramétrable (`no_return_ratio`) de
  décrochages sporadiques remplace des distances valides.
- Compter ouvertures et fermetures (le service doit fermer le flux dans tous les cas).

## Design

- Ordre de réception comme la file de l'adaptateur réel : les distances arrivées
  pendant qu'on ne lisait pas sortent tout de suite, avec leur heure d'arrivée.
- Co-localisé avec l'adaptateur réel (`infrastructure/hardware/lsm9ds1/fake/`).
