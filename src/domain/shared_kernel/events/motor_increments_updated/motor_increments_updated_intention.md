# motor_increments_updated — Intention

## Rationale

`PositionUpdated` porte une position en millimètres : il n'existe pas tant que le
banc n'a pas de conversion mm/impulsion. Or c'est précisément quand le banc n'est
pas calibré — et pendant sa calibration par barre — que l'opérateur doit voir où est
le moteur : en incréments, la grandeur que la calibration mesure (n₁, n₂). Sans
événement en incréments, l'écran resterait figé pendant toute la calibration.

## Responsibility

- Annoncer que la position moteur, en incréments comptés par le contrôleur, a changé
  (X, Y, en mouvement ou non).

## Design

- Publié par le moniteur de position de l'adaptateur Arcus à chaque changement,
  calibré ou non ; `PositionUpdated` (mm) n'est publié que si la conversion existe.
- Topic : `motorincrementsupdated`.
- Pas d'unité à préciser au-delà du nom : l'incrément moteur est l'unité du
  contrôleur, sans conversion.
