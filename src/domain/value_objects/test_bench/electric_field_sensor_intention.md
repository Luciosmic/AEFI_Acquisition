# electric_field_sensor (CubicSensor3D) — Intention

## Rationale

Value object représentant le capteur de champ électrique 3D cubique du banc d'essai. Encapsule les propriétés géométriques et de sensibilité du capteur qui sont nécessaires pour la modélisation de la réponse.

## Responsibility

- Stocker les propriétés du capteur : dimensions, position, orientation, sensibilité par axe.
- Servir de type pour le champ `sensor` de `TestBench`.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans `TestBench.configure_geometry()` et potentiellement dans `AefiPhysicsEngine`.
