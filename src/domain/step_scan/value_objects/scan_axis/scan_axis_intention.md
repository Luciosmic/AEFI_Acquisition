# scan_axis — Intention

## Rationale

Nommer explicitement l'axe rapide (fast axis) des patterns RASTER et SERPENTINE, pour éviter d'encoder cet ordre en dur dans le générateur de trajectoire.

## Responsibility

- `Y` : balayage colonnes Y d'abord (outer=X, inner=Y) — comportement par défaut préféré.
- `X` : balayage lignes X d'abord (outer=Y, inner=X) — comportement legacy.

## Design

- `Enum` simple, sans état ni logique.
