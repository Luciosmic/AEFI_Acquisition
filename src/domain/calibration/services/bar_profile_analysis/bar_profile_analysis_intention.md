# bar_profile_analysis — Intention

## Rationale

Le LIDAR et le moteur ne partagent aucune horloge : pendant le fly scan, les
distances arrivent par le flux LIDAR (~25 Hz), les positions par interrogation du
contrôleur. Sans règle d'appariement explicite, chaque distance serait associée à
« la dernière position lue », avec une erreur qui dépend de l'ordre des lectures et
change d'un banc à l'autre. Et sans analyse du profil dans le domaine, les plateaux,
le seuil et les fronts grossiers seraient calculés dans le service applicatif, hors
de portée des tests sur créneaux synthétiques bruités — or c'est exactement là que se
cachent les cas limites (barre qui touche une butée, deuxième zone courte, contraste
nul).

## Responsibility

- `pair_by_reception_time(positions, samples)` : associer à chaque distance la
  position interpolée linéairement à son instant de réception (modèle du fly scan
  du scan : deux flux horodatés à la réception, appariés par le temps). Les
  distances hors de l'intervalle couvert par les positions sont écartées.
- `locate_bar(profile, min_contrast_mm)` : à partir des couples (incrément,
  distance), estimer les plateaux (médianes de part et d'autre d'un seuil
  provisoire), le seuil s, le bruit des plateaux et les deux fronts grossiers
  (milieu entre le dernier point hors barre et le premier point sur la barre, et
  inversement). Refuser (`BarProfileUnusableError`) un profil sans contraste, une
  barre qui touche une extrémité de la course, ou plusieurs zones courtes.

## Design

- Fonctions pures, sans état ni I/O (entrées/sorties).
- La latence du LIDAR décale les fronts grossiers ; elle n'est pas corrigée ici :
  la marge de l'encadrement l'absorbe, et l'affinage à l'arrêt n'en dépend pas.
- Plateaux par médianes (robustes aux points de transition) ; seuil provisoire au
  milieu des percentiles 5 et 95, puis seuil final au milieu des plateaux.
- La barre est la plus longue suite continue de points sur la barre : un point isolé
  basculé par le bruit sur un plateau ne crée pas de faux front. Au-delà de 5 % de
  points « sur la barre » hors de cette suite, le profil est refusé (deuxième objet
  sous le LIDAR).
- Bruit des plateaux : écart absolu médian × 1,4826 (estimateur robuste de σ), le
  plus grand des deux plateaux ; donné à l'opérateur, pas utilisé pour classer.
