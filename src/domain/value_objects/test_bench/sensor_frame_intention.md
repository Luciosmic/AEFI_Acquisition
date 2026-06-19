# sensor_frame — Intention

## Rationale

Value object définissant le repère de référence du capteur cubique dans l'espace du banc. Permet de calculer les composantes de champ dans le repère du capteur plutôt que dans le repère monde.

## Responsibility

- Stocker la position et l'orientation du capteur dans le repère du banc.
- Fournir les informations nécessaires pour la projection des vecteurs champ dans le repère capteur.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans `TestBench` et `AefiPhysicsEngine` pour les transformations de repère.
