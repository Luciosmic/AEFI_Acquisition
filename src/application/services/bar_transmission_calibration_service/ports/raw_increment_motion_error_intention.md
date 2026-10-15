# raw_increment_motion_error — Intention

## Rationale

Sans erreur déclarée par le port, le service de calibration devrait attraper les
exceptions du driver Arcus (pylablib, port série) : il dépendrait de
l'infrastructure, et un Fake ne pourrait pas reproduire la même défaillance.

## Responsibility

- Seule erreur levée par `IRawIncrementMotionPort` : contrôleur ou liaison en échec,
  ou attente d'arrêt dépassée.

## Design

- `RuntimeError` nommée, levée par l'adaptateur Arcus et par le Fake ; traduite en
  erreur de cas d'usage par `BarTransmissionCalibrationService`.
