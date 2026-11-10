# source_frame_solver — Intention

## Rationale

Les centres des sphères ne sont pas accessibles au pied à coulisse : sans
reconstruction, l'appli ne connaît que 6 distances et 4 diamètres. Le problème
direct 4 sphères doit alors supposer un carré parfait, l'export ne peut pas
dire où sont réellement les sources, et une erreur de saisie (chiffres
inversés) passe inaperçue tant qu'elle ne fait pas chevaucher deux sphères.
Tant que ce calcul vivait dans `external_modules/source_geometry/`, il avait
son propre ordre des distances (`D_12, D_13, …`) et son propre repère : deux
langages pour un même concept, et aucun moyen pour l'UI (interface
utilisateur) ou l'export de l'appeler.

## Responsibility

- `solve(entry) -> SourceFrameGeometry` : à partir d'une
  `SourceGeometryCalibrationEntry`, placer les 4 centres dans le repère source
  (centroïde, x/y le long des côtés du carré ajusté, quadrants
  `x_neg_y_pos`…), ajuster le carré parfait, calculer
  les résidus par distance.
- Refuser (`SourceGeometryInconsistentError`) des mesures qu'aucune
  configuration plane ne satisfait.

## Design

Domain service sans état (méthode statique), pas d'I/O (entrées/sorties) ;
`numpy` + `scipy` (bibliothèques stables, acceptées dans le domain). Le calcul
enchaîne trois étapes, chacune répondant à une question différente.

### 1. Où sont les centres ? — reconstruction à partir des distances

- Coplanarité imposée (z=0) : contrainte connue de la source, pas une
  hypothèse. Laisser la hauteur de S4 libre donnait un discriminant négatif
  sur les mesures réelles : un problème mal posé, pas un signe de non-planéité.
- 6 distances mesurées pour 5 degrés de liberté (4 centres dans le plan moins
  un déplacement rigide) : une mesure redondante, donc des mesures jamais
  parfaitement cohérentes entre elles. Il faut répartir cette incohérence.
- Graine par élimination exacte (S1 à l'origine, S2 sur x, S3 par le
  triangle, S4 contre S1 et S2), puis moindres carrés non linéaires sur
  **les 4 centres et les 6 distances**. Ajuster S4 seul faisait porter toute
  l'incohérence sur S4 : une saisie symétrique (côtés 85 mm, diagonales
  110 mm) donnait un quadrilatère déformé d'un seul côté (corrigé le
  2026-10-01).

### 2. Dans quel repère les exprimer ? — orientation

Le repère de travail de l'étape 1 (S1 à l'origine, S2 sur x) est arbitraire et
reste interne ; seul le repère source sort du service. On y passe par deux
rotations rigides, qui ne changent ni les distances ni les résidus :

- les milieux de côtés donnent l'orientation des quadrants et lèvent
  l'ambiguïté miroir (les distances seules ne distinguent pas une
  configuration de son reflet) ;
- puis une rotation aligne le carré ajusté (étape 3) sur x et y. Aligner sur
  les seuls milieux de côtés privilégiait les côtés S1-S3/S4-S2 : sur les
  mesures réelles le carré ajusté sortait tourné de 0,7° (moitié du
  cisaillement de l'arrangement, ~1,4°).

### 3. De combien s'écarte-t-on d'un carré parfait ? — ajustement du carré

La source est conçue comme un carré : il faut le carré parfait le plus proche
des 4 centres pour mesurer l'écart de fabrication et orienter le repère.

- Formule fermée en nombres complexes. On parcourt le périmètre
  S1→S3→S2→S4 (S1-S2 et S3-S4 sont les diagonales) ; sur un carré parfait,
  passer d'un coin au suivant revient à tourner de 90° autour du centre, donc
  le coin k vaut `centre + z0 · i^(-k)`, où `z0` porte à la fois la taille et
  l'orientation du carré.
- Le meilleur carré au sens des moindres carrés s'obtient par simple
  projection : `centre` = moyenne des 4 points, `z0` = moyenne des points
  « dé-tournés » de 90° à chaque coin. Les deux motifs (constant et rotation
  de 90°) sont orthogonaux sur 4 points, d'où une solution exacte, unique, en
  une passe — pas de graine, pas d'itération, pas de minimum local.
  (Mathématiquement, `z0` est un coefficient de la DFT — Discrete Fourier
  Transform, transformée de Fourier discrète — des 4 coins ; c'est le seul
  lien avec le traitement du signal.)
- Le sens de parcours compte : S1→S3→S2→S4 tourne dans le sens horaire dans
  le repère source, soit -90° par coin. Projeter sur la rotation dans le
  mauvais sens renvoie une composante quasi nulle (« côté » de ~1 mm au lieu
  de ~64 mm sur les mesures réelles), sans erreur visible.
- Alternatives écartées : Procrustes par SVD (Singular Value Decomposition,
  décomposition en valeurs singulières), même résultat mais matrices et cas
  de réflexion à gérer ; `least_squares` itératif, non exact et dépendant
  d'une graine.

### Historique

Validé dans `external_modules/source_geometry/` (2026-07-24 → 2026-07-29),
résultats identiques au µm près sur les mesures réelles du 2026-07-24 au
moment de l'intégration.
