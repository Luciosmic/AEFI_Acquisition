# bar_profile_unusable_error — Intention

## Rationale

Un profil de fly scan peut ne pas contenir de créneau exploitable : barre absente
ou hors de la trajectoire du LIDAR, barre qui dépasse la course (pas de plateau hors
barre d'un côté), plusieurs zones courtes (obstacle, barre mal posée). Sans erreur
nommée, l'analyse rendrait des fronts absurdes et l'affinage passerait de longues
minutes à encadrer un front qui n'existe pas, ou rendrait une transmission fausse.

## Responsibility

- Nommer le refus : le profil mesuré ne montre pas une barre unique, entièrement
  dans la course, avec un plateau hors barre de chaque côté.
- Porter la raison lisible par l'opérateur (quoi corriger sur le banc).

## Design

- Exception du domaine, comme `SensorResponseDegenerateError` : levée par
  `bar_profile_analysis.locate_bar`, traduite par le service applicatif en erreur
  de cas d'usage. Aucune notion d'infrastructure (port série, LIDAR) dedans.
