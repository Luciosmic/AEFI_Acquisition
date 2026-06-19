# transformation_events — Intention

## Rationale

Modéliser les événements liés aux transformations de repère du capteur. Permettent à la UI de mettre à jour la visualisation 3D (CubeVisualizer) en réaction aux rotations appliquées, via le bus événementiel.

## Responsibility

- Événements signalant l'application d'une rotation ou transformation de frame au capteur.
- Porter les paramètres de transformation (quaternion ou angles d'Euler) pour la reconstruction côté UI.

## Design

- **`@dataclass`** héritant de `DomainEvent`.
- Publiés par `TransformationService` après chaque transformation appliquée.
