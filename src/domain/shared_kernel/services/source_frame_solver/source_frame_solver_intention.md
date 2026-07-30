# source_frame_solver — Intention

## Rationale

Implémente la reconstruction DGP (voir "NOTE - Source Frame Geometry", vault Luis Saluden, hors dépôt, §3-4) des positions des 4 sphères excitatrices depuis les distances centre-à-centre dérivées de `SourceGeometry`. Les 4 sphères sont coplanaires **par construction du banc** — une contrainte connue a priori, pas une hypothèse à vérifier après coup — donc toutes les positions sont résolues directement dans le plan z=0.

**Piège identifié (2026-07) :** la version initiale traitait z4 comme une inconnue libre résolue via $z_4=\sqrt{d_{14}^2-x_4^2-y_4^2}$. Avec des mesures réelles bruitées, ce discriminant devient négatif — pas un vrai signe de non-coplanarité, mais l'artefact d'un problème mal posé : le bruit de mesure (3ᵉ distance redondante $d_{34}$) était injecté dans une dimension fictive plutôt que d'être moyenné. Une fois la coplanarité posée comme contrainte a priori, S4 a 3 distances mesurées ($d_{14}, d_{24}, d_{34}$) pour 2 inconnues ($x_4,y_4$) — système réellement sur-déterminé en 2D. Une naïve régression linéaire sur les 3 équations de différence de cercles ne résout PAS correctement ce problème (la 3ᵉ ligne est une combinaison linéaire exacte des deux autres en coefficients — testé numériquement, résidu ~1000x pire que l'optimum). Seule une régression non linéaire (moindres carrés) sur les 3 équations de distance d'origine utilise correctement la mesure redondante.

## Responsibility

- `solve(geometry: SourceGeometry, degeneracy_tolerance=1e-4, orthogonality_tolerance=1e-3) → SourceFrameGeometry`.
- Ancrer S1 à l'origine, S2 sur l'axe x, résoudre S3 dans le plan xy (système exact, 2 équations/2 inconnues).
- Résoudre S4 par moindres carrés non linéaires (`scipy.optimize.least_squares`) sur les 3 équations de distance à S1/S2/S3 — initialisé par la solution exacte des 2 premières, raffiné pour intégrer la 3ᵉ.
- Lever `ValueError` si le triangle S1-S2-S3 est géométriquement impossible (racine négative au-delà de la tolérance).
- Calculer le référentiel source canonique : centroïde, axes (x: S2→S1, y: S4→S3, z: x∧y), matrice de rotation (colonnes = axes).
- Flaguer `is_orthogonal` (axes x/y quasi perpendiculaires) sans forcer d'orthonormalisation.

## Design

- Service domain stateless (`@staticmethod`), pas d'I/O — pattern `ScanTrajectoryFactory`.
- `numpy` pour l'algèbre linéaire (norme, produit vectoriel), `scipy.optimize.least_squares` pour le raffinement de S4 — les deux sont des dépendances projet existantes (calcul pur, pas de l'infrastructure).
- Sortie convertie en tuples immuables (`SourceFrameGeometry`), z=0 pour toutes les positions.
