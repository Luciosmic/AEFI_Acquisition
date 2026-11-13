---
type: atome::solidai-atome
tldr: "Erreur `raw_increment_motion_error` : Seule erreur levée par `IRawIncrementMotionPort` : contrôleur ou liaison en échec, ou attente d'arrêt dépassée."
code: ["[[src/application/test_bench_calibration/raw_increment_motion/ports/raw_increment_motion_error.py]]"]
cause_de_changement: orchestration
---
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
  erreur de cas d'usage par le service applicatif qui consomme le port.
