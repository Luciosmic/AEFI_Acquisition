# source_frame_solver — Intention

## Rationale

Les centres des sphères ne sont pas accessibles au pied à coulisse : sans
reconstruction, l'appli ne connaît que 6 distances et 4 diamètres. Le problème
direct 4 sphères doit alors supposer un carré parfait, l'export ne peut pas
dire où sont réellement les sources, et une erreur de saisie (chiffres
inversés) passe inaperçue tant qu'elle ne fait pas chevaucher deux sphères.
Tant que ce calcul vivait dans `external_modules/source_geometry/`, il avait
son propre ordre des distances (`D_12, D_13, …`) et son propre repère : deux
langages pour un même concept, et aucun moyen pour l'UI ou l'export de
l'appeler.

## Responsibility

- `solve(entry) -> SourceFrameGeometry` : à partir d'une
  `SourceGeometryCalibrationEntry`, placer les 4 centres dans le repère source
  (centroïde, quadrants `x_neg_y_pos`…), ajuster le carré parfait, calculer
  les résidus par distance.
- Refuser (`SourceGeometryInconsistentError`) des mesures qu'aucune
  configuration plane ne satisfait.

## Design

- Domain service sans état (méthode statique), pas d'I/O ; `numpy` + `scipy`
  (bibliothèques stables, acceptées dans le domain).
- Coplanarité imposée (z=0) : contrainte connue du banc, pas une hypothèse.
- Graine par élimination exacte (S1, S2, S3 puis S4), puis moindres carrés
  non linéaires sur **les 4 centres et les 6 distances** (6 mesures pour 5
  degrés de liberté). Ajuster S4 seul faisait porter toute l'incohérence des
  mesures sur S4 : une saisie symétrique (côtés 85 mm, diagonales 110 mm)
  donnait un quadrilatère déformé d'un seul côté (corrigé le 2026-10-01).
- Repère de travail (S1 à l'origine, S2 sur x) purement interne ; seul le
  repère source sort du service.
- Carré ajusté par DFT 4 points sur le périmètre S1→S3→S2→S4 (sens horaire
  dans le repère source ⇒ générateur w=-i).
- Historique : validé dans `external_modules/source_geometry/`
  (2026-07-24 → 2026-07-29), résultats identiques au µm près sur les mesures
  réelles du 2026-07-24 au moment de l'intégration.
