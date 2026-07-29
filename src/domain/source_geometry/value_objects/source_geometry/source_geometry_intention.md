# source_geometry — Intention

## Rationale

Ce qu'on peut mesurer directement sur le banc AEFI 4 sphères, ce sont des distances relatives entre centres de sphères (au pied à coulisse) — jamais leurs coordonnées dans un référentiel global. `SourceGeometry` porte cette donnée brute mesurable, telle quelle. Voir `config_templates/NOTE - Source Frame Geometry.md`.

## Responsibility

- Stocker les 6 distances centre-à-centre `d_12, d_13, d_14, d_23, d_24, d_34` (mètres).
- Valider que chaque distance est finie et strictement positive.
- Servir d'entrée à `SourceFrameSolver.solve()` (reconstruction DGP).

## Design

- `@dataclass(frozen=True)` — immuable.
- Pas de logique de reconstruction ici : la validation géométrique fine (triangle dégénéré, coplanarité) est de la responsabilité du solveur, pas de ce VO — cette classe ne garantit que la positivité des mesures brutes.
