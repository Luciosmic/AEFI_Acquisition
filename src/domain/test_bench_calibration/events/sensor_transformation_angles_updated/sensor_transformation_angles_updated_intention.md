---
type: evenement-de-domaine::solidai-ddd
tldr: "Signale l'application d'une rotation ou transformation de frame au capteur."
code: ["[[src/domain/test_bench_calibration/events/sensor_transformation_angles_updated/sensor_transformation_angles_updated.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_calibration/calibration_intention]]"
---
# sensor_transformation_angles_updated — Intention

## Rationale

Modéliser l'événement lié aux transformations de repère du capteur. Permet à la UI de réagir aux rotations appliquées, via le bus événementiel.

## Responsibility

- Signale l'application d'une rotation ou transformation de frame au capteur.
- Porte les paramètres de transformation (angles d'Euler) pour la reconstruction côté UI.

## Design

- **`@dataclass`** héritant de `DomainEvent`.
- Publié par `TransformationService` après chaque transformation appliquée.
