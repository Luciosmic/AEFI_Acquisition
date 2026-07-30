# source_geometry

Reconstruit les positions des 4 sphères excitatrices AEFI depuis les distances
mesurées au pied à coulisse (Distance Geometry Problem), et visualise l'écart
au carré parfait.

## Pourquoi ici et pas dans `src/`

Ce n'est pas encore un aggregate DDD (pas de racine, pas d'identité, pas
d'invariant propre à protéger derrière un cycle de vie) — juste des calculs
purs et une visualisation, en aval de l'appli d'acquisition. Le sortir de
`src/` maintenant ne coûte rien et laisse le développement itérer librement,
sans être contraint par les standards DDD/Packmind du cœur applicatif. Une
intégration plus poussée (API appelée depuis l'appli) pourra venir plus tard
si le besoin se confirme.

## Contenu

- `source_geometry.py` — VO : grandeurs brutes mesurées (`D_ij` extrémité-à-
  extrémité, `phi_i` diamètre par sphère). `r_i` et `d_ij` (centre-à-centre)
  exposés en propriétés dérivées, jamais stockées.
- `source_frame_solver.py` — reconstruction DGP coplanaire : S1/S2/S3 par
  élimination exacte, S4 par moindres carrés non linéaires (3 distances
  mesurées pour 2 inconnues — voir docstring pour l'historique du bug corrigé).
- `source_frame_geometry.py` — VO résultat : positions (z=0), centroïde, axes,
  matrice de rotation.
- `visualize_square_deviation.py` — rapport chiffré + schéma : les 4 sphères
  sont posées aux coins d'un carré (S1↔S2 et S3↔S4 sont les diagonales,
  S1→S3→S2→S4 trace le périmètre) ; le carré parfait le mieux ajusté est
  calculé par décomposition harmonique (DFT à 4 points), l'écart résiduel
  quantifie le défaut mécanique réel du banc.

## Usage

```
uv run python external_modules/source_geometry/visualize_square_deviation.py
```

Lit `config_templates/aefi_device_config.json` par défaut.

## Historique notable

- Le solveur traitait initialement la hauteur de S4 comme une inconnue libre
  (le problème DGP général suppose une position 3D a priori inconnue),
  résolue puis vérifiée après coup. Avec des mesures réelles, ça produisait
  un discriminant négatif — pas un signe de non-planéité, mais l'artefact
  d'un problème mal posé : les 4 sphères sont coplanaires **par construction
  du banc**, une contrainte connue a priori. Fix : toutes les positions sont
  résolues avec z=0 imposé, S4 par moindres carrés sur les 3 distances qui
  le contraignent (voir docstring de `source_frame_solver.py`).
- Le premier essai de `fit_square()` (décomposition harmonique) utilisait la
  convention de rotation inverse (sens antihoraire au lieu d'horaire pour
  l'ordre S1→S3→S2→S4 dans le repère du solveur) — résultat silencieusement
  faux (~1mm de "côté" au lieu de ~64mm). Corrigé et couvert par
  `_tests/visualize_square_deviation_test.py::test_winding_direction_matches_solver_frame`.
