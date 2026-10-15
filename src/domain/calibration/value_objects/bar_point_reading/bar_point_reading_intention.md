# bar_point_reading — Intention

## Rationale

Près d'un front, le spot du LIDAR voit à la fois la barre et le sol : la distance
moyenne passe par le seuil et le bruit du LIDAR décide seul du côté. Sans lecture
de point explicite, la décision « sur la barre / hors barre » se réduirait à une
comparaison `d < s` : un point dans le bruit serait classé au hasard, la dichotomie
continuerait sur une fausse information et l'incertitude annoncée serait trop
petite. Il faut un troisième verdict, **indécidable**, qui arrête l'affinage à la
limite réelle de la mesure.

## Responsibility

- Résumer les k échantillons LIDAR pris à l'arrêt en un point : moyenne d̄,
  écart-type σ, nombre k.
- Classer le point par rapport au seuil s :
  - **indécidable** si |d̄ − s| < k_σ · σ / √k (ou si d̄ = s) ;
  - **sur la barre** si d̄ < s (la barre est plus proche du LIDAR que le sol) ;
  - **hors barre** sinon.

## Design

- Value object immuable ; `from_samples` exige au moins 2 échantillons (σ doit
  exister).
- σ est l'écart-type de l'échantillon du point lui-même (ddof = 1) : près du bord,
  le bruit augmente et la zone indécidable s'élargit d'elle-même.
- L'unité du LIDAR n'est pas vérifiée : seul le seuil compte, la classification
  n'en dépend pas.
- `BarPointClassification` (sur la barre / hors barre / indécidable) vit ici : c'est
  le verdict de cette lecture.
