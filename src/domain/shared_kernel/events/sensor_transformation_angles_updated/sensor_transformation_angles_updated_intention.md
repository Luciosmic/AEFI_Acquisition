# sensor_transformation_angles_updated — Intention

## Rationale

Modéliser l'événement lié aux transformations de repère du capteur. Permet à la UI de mettre à jour la visualisation 3D (CubeVisualizer) en réaction aux rotations appliquées, via le bus événementiel.

## Responsibility

- Signale l'application d'une rotation ou transformation de frame au capteur.
- Porte les paramètres de transformation (angles d'Euler) pour la reconstruction côté UI.

## Design

- **`@dataclass`** héritant de `DomainEvent`.
- Publié par `TransformationService` après chaque transformation appliquée.
