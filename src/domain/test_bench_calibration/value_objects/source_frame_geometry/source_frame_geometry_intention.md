# source_frame_geometry — Intention

## Rationale

Le pied à coulisse ne mesure que des distances extrémité-à-extrémité et des
diamètres. Sans un résultat de reconstruction nommé dans le domain, les
positions des sphères n'existent nulle part dans le système : l'export JSON ne
peut pas les porter, le problème direct 4 sphères doit supposer un carré
parfait (`PointChargeFieldSimulator`), et l'écart réel de l'arrangement des
sphères au carré reste invisible. Avant cette intégration, ce résultat vivait dans
`external_modules/source_geometry/` avec un second repère (S1 à l'origine, S2
sur x) et un second ordre des distances — deux langages pour un même concept.

## Responsibility

- Porter les positions des centres S1..S4 dans **le** repère source (centroïde
  à l'origine, x/y le long des côtés du carré ajusté — idéalement la source
  est un carré aligné sur les axes —, chaque sphère dans son quadrant
  `x_neg_y_pos`…).
- Porter le carré parfait le mieux ajusté (coin idéal par sphère, côté) et
  exposer l'écart au carré (par sphère, RMS).
- Porter les résidus de reconstruction par distance (cohérence des 6 mesures).

## Design

- `@dataclass(frozen=True)`, tuples de floats (vraiment immuable).
- Ordres : sphères S1..S4 ; distances dans l'ordre de
  `SourceGeometryCalibrationEntry.pairwise_distances_ext` (`D_S1_S2, D_S3_S4,
  D_S1_S3, D_S1_S4, D_S2_S3, D_S2_S4`).
- Positions 2D : z=0 par construction de la source, pas une hypothèse à vérifier.
- Construit uniquement par `SourceFrameSolver.solve()`.
