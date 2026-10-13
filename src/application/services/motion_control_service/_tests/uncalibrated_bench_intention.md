# uncalibrated_bench_test — Intention

## Rationale

Sans ce test, l'état « non calibré » redevient une exception au démarrage, ou une valeur par défaut silencieuse qui fait bouger le banc de façon fausse, ou un bandeau qui ne disparaît jamais après la saisie.

## Responsibility

- Le démarrage sans « Pas par tour » ne lève pas et nomme la grandeur manquante.
- Mouvements et homing sont refusés par `MotionConversionUnavailable` avant d'atteindre le port ; arrêts toujours possibles.
- La saisie de la grandeur applique la conversion en direct ; une conversion déjà appliquée n'est jamais changée en session.
