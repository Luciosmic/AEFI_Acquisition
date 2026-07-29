# source_frame_solver — Intention

## Rationale

Implémente l'algorithme analytique exact du DGP (`config_templates/NOTE - Source Frame Geometry.md` §3) pour reconstruire les positions des 4 sphères excitatrices depuis les 6 distances pairwise mesurées au pied à coulisse. C'est ce calcul qui rend les distances mesurables exploitables comme référentiel de positionnement.

## Responsibility

- `solve(geometry: SourceGeometry, degeneracy_tolerance=1e-4, coplanarity_tolerance=1e-4, orthogonality_tolerance=1e-3) → SourceFrameGeometry`.
- Ancrer S1 à l'origine, S2 sur l'axe x, résoudre S3 dans le plan xy puis S4 en 3D (système linéaire + racine, signe z4 ≥ 0 par convention).
- Lever `ValueError` si un triangle est géométriquement impossible (distances incompatibles — racine négative).
- Calculer le référentiel source canonique : centroïde, axes (x: S2→S1, y: S4→S3, z: x∧y), matrice de rotation (colonnes = axes).
- Flaguer `is_coplanar` (|z4| < tolérance) et `is_orthogonal` (axes x/y quasi perpendiculaires) sans forcer d'orthonormalisation — les axes bruts restent l'indicateur du défaut d'alignement mécanique.

## Design

- Service domain stateless (`@staticmethod`), pas d'I/O — pattern `ScanTrajectoryFactory`.
- Utilise `numpy` pour l'algèbre linéaire (norme, produit vectoriel) ; sortie convertie en tuples immuables (`SourceFrameGeometry`).
