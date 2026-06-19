# position_3d — Intention

## Rationale

Extension de `Position2D` avec une coordonnée Z pour les opérations 3D du banc d'essai et de la physique AEFI. Nécessaire pour les calculs de distance source-capteur dans le problème direct.

## Responsibility

- Stocker `x: float`, `y: float`, `z: float` en millimètres.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans les contexts où la hauteur Z est pertinente (bench geometry, physics engine).
