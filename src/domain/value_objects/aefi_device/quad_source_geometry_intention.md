# quad_source_geometry — Intention

## Rationale

Value object décrivant la géométrie à quatre quadrants de sources de l'instrument AEFI (disposition en carré autour du capteur central). Encapsuler la géométrie dans un type dédié permet le calcul des positions locales de chaque source par quadrant.

## Responsibility

- Stocker les paramètres géométriques de l'arrangement quadrant : rayon, hauteur, orientation du capteur.
- Fournir `get_source_local_pos(quadrant: Quadrant) → Vector3D` pour récupérer la position locale d'une source.
- Définir l'enum `Quadrant` (TOP_RIGHT, TOP_LEFT, BOTTOM_LEFT, BOTTOM_RIGHT).

## Design

- **`@dataclass(frozen=True)`** : la géométrie de l'instrument est fixe.
- Utilisé par `AefiDevice.get_interactions()` via le mapping `source_id → Quadrant`.
