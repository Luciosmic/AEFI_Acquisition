# frame_rotation — Intention

## Rationale

Value object encapsulant une rotation de repère de référence pour le capteur 3D cubique. Utilisé par `TransformationService` pour appliquer des rotations (ex. calibration d'orientation) aux mesures de champ électrique.

## Responsibility

- Stocker les paramètres d'une rotation (angles d'Euler ou quaternion selon l'implémentation).
- Servir de type de configuration pour les panneaux de transformation dans la UI.

## Design

- **`@dataclass(frozen=True)`**.
- Consommé par `TransformationService` et le `SensorTransformationPanel`.
