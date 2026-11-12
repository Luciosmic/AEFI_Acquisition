# fake_acquisition_conditions_port — Intention

## Rationale

Le lecteur réel des conditions interroge le catalogue des composants sur
disque, la mémoire des contrôleurs, les services de calibration et les
moteurs. Sans double en mémoire, les tests du service de caractérisation
devraient monter tout le banc (ou le simuler) pour vérifier le document de
paramètres, et ne pourraient pas reproduire un moteur déconnecté.

## Responsibility

- `make_bench_conditions()` : un banc plausible (tous les composants
  montés, bruit ADC non caractérisé, AD9106 coupé, capteur aux angles
  idéaux, MCU sur COM10).
- Rendre les conditions données ; rendre les positions données dans
  l'ordre (début, fin) ; `position_failure` reproduit l'échec du réel
  (moteurs non connectés).

## Design

- Vérification d'état (`conditions_reads`), pas d'interactions.
- Même mode d'échec que le réel : position → `OperationResult.fail` ; un
  fait inconnu → champ `None` + `unknown` dans le DTO fourni.
- Lecture instantanée : le réel est une lecture mémoire / petits fichiers,
  aucune régulation ne dépend de sa latence.
