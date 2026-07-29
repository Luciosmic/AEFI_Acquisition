# source_frame_geometry — Intention

## Rationale

Résultat immuable de la reconstruction DGP (Distance Geometry Problem) : les positions cartésiennes des 4 sphères et le référentiel source canonique qu'elles définissent (centroïde, axes, rotation). Voir `config_templates/NOTE - Source Frame Geometry.md` §3-4.

## Responsibility

- Stocker `positions` (P1..P4, tuples (x,y,z) mètres) dans le référentiel d'ancrage du solveur (S1 à l'origine, S2 sur l'axe x).
- Stocker `centroid`, `x_axis`, `y_axis`, `z_axis` (vecteurs unitaires) et `rotation_matrix` (colonnes = axes) qui définissent le référentiel source canonique.
- Exposer `is_coplanar` et `is_orthogonal` (flags calculés par le solveur selon des seuils de tolérance).

## Design

- `@dataclass(frozen=True)` — pure donnée, aucune méthode de calcul.
- Construit exclusivement par `SourceFrameSolver.solve()` — jamais instancié à la main en dehors des tests.
- Tuples de floats (pas numpy) pour rester réellement immuable et hashable.
