# adapter_raw_increment_motion_arcus — Intention

## Rationale

Le seul chemin vers le moteur sans conversion mm/impulsion passe par le driver
Arcus (précédent : `characterization/motion_timing_characterizer.py`). Sans
adaptateur, le service de calibration importerait le driver, attraperait ses
exceptions pylablib et ne pourrait jamais tourner sur un Fake.

## Responsibility

- Implémenter `IRawIncrementMotionPort` sur `ArcusPerformax4EXController` (ou le
  `FakeArcusPerformax4EXController` en mode mock).
- Butée + : `jog(axe, "+")` ; le contrôleur s'arrête seul sur le fin de course
  physique (pylablib laisse les erreurs de limite désactivées : l'axe limité
  s'arrête, les autres continuent). L'atteinte est lue dans le bit `sw_plus_lim` du
  registre d'état (`MST`), via `is_at_limit`.
- Traduire toute exception du driver en `RawIncrementMotionError`.

## Design

- Partage le contrôleur avec `ArcusAdapter` (port mm) : le driver sérialise chaque
  échange par RLock, donc le moniteur de position de `ArcusAdapter` reste actif
  (affichage des incréments pendant la calibration). Contrairement au
  caractériseur, on ne désactive pas l'adaptateur mm : la mesure fine se fait à
  l'arrêt et la latence de lecture ne touche que le repérage grossier.
- `wait_until_stopped` interroge `is_moving` toutes les 20 ms au lieu de
  `wait_move` du driver, qui garde le verrou pendant toute l'attente.
- `home` reste bloquant et garde le verrou du driver pendant le homing (comme le
  worker de `ArcusAdapter`) : le moniteur attend la fin du homing.
