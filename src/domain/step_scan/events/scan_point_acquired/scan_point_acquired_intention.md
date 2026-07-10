# scan_point_acquired — Intention

## Rationale

Modéliser l'acquisition d'un point de scan comme un fait immuable passé, avec la donnée brute nécessaire à la mise à jour temps réel de la carte 2D.

## Responsibility

- `scan_id` : identifiant du scan.
- `point_index` : index du point acquis.
- `position` : `Position2D` du point.
- `measurement` : `VoltageMeasurement` complète — évite un second accès à l'agrégat depuis la UI.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
