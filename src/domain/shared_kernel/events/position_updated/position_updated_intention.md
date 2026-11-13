---
type: evenement-de-domaine::solidai-ddd
tldr: "Événement `position_updated` : `position` : `Position2D` courante du système de motion."
code: ["[[src/domain/shared_kernel/events/position_updated/position_updated.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# position_updated — Intention

## Rationale

Modéliser la mise à jour de la position courante du système de motion comme un fait immuable passé, pour la mise à jour temps réel de la UI.

## Responsibility

- `position` : `Position2D` courante du système de motion.
- `is_moving` : indique si le système est en cours de déplacement.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Publié en continu (polling hardware) par l'adaptateur Arcus, consommé par `MotionPresenter` pour l'affichage temps réel.
