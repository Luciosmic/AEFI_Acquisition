# vector_3d (domain/value_objects/geometric) — Intention

## Rationale

Value object vectoriel 3D dans la couche value_objects/geometric — version formelle pour les calculs de direction, normale et rotation dans les contextes géométriques de la couche value_objects. Distinct de `domain/shared/vector_3d` utilisé directement par les agrégats.

## Responsibility

- Représenter un vecteur 3D avec opérations algébriques (norm, dot, cross, normalize).

## Design

- **`@dataclass(frozen=True)`**.
- Co-localisé dans `geometric/` pour regrouper les types géométriques du domain.
