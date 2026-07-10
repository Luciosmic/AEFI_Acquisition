# position_updated — Intention

## Rationale

Modéliser la mise à jour de la position courante du système de motion comme un fait immuable passé, pour la mise à jour temps réel de la UI.

## Responsibility

- `position` : `Position2D` courante du système de motion.
- `is_moving` : indique si le système est en cours de déplacement.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Publié en continu (polling hardware) par l'adaptateur Arcus, consommé par `MotionPresenter` pour l'affichage temps réel.
