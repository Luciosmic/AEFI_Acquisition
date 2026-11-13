---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_adapter_raw_increment_motion_arcus` : Implémenter `IRawIncrementMotionPort` en mémoire : deux axes, mouvement linéaire dans le temps de l'horloge injectée (`FakeClock` en test, temps réel sinon), butée + à `plus_limit_increments`."
code: ["[[src/infrastructure/hardware/arcus_performax_4ex/adapter_raw_increment_motion_arcus/fake/fake_adapter_raw_increment_motion_arcus.py]]"]
cause_de_changement: outil
implements: ["[[src/application/test_bench_calibration/raw_increment_motion/ports/i_raw_increment_motion_port_intention]]"]
double_de: "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_raw_increment_motion_arcus/adapter_raw_increment_motion_arcus_intention]]"
---
# fake_adapter_raw_increment_motion_arcus — Intention

## Rationale

Le service de calibration par barre doit être testé sans banc. L'adaptateur réel
sur `FakeArcusPerformax4EXController` tourne en temps réel : un fly scan de butée à
butée y dure plus d'une minute. Un Mock d'interactions ne verrait pas l'essentiel :
la position change **pendant** que le LIDAR échantillonne. Il faut un Fake qui
bouge dans le temps, mais dans un temps qu'on peut accélérer.

## Responsibility

- Implémenter `IRawIncrementMotionPort` en mémoire : deux axes, mouvement linéaire
  dans le temps de l'horloge injectée (`FakeClock` en test, temps réel sinon),
  butée + à `plus_limit_increments`.
- Reproduire les modes de défaillance du réel : `RawIncrementMotionError` sur une
  opération (`fail_on`), axe arrêté en fin de course sans fin de course lu
  (`limit_switch_present=False`), attente d'arrêt dépassée.

## Design

- Vitesse par défaut : 800 incréments/s, le préréglage « slow » mesuré au banc
  (797,7 incréments/s, `fake_arcus_performax4ex_controller`). Le temps mort t0 des
  mouvements n'est pas simulé : la calibration ne dépend que de la position pendant
  le mouvement, pas de la durée exacte d'un déplacement court.
- Homing instantané (contrat bloquant) : sa durée n'a pas d'effet sur la mesure.
- Co-localisé avec l'adaptateur réel (`infrastructure/hardware/arcus_performax_4ex/fake/`).
