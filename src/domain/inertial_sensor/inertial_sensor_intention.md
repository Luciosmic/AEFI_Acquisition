# inertial_sensor — Intention

## Rationale

Le banc doit un jour attendre sa stabilisation mécanique avant une mesure de
scan, et le capteur inertiel (accéléromètre, gyroscope, magnétomètre) est ce
qui la révélera. Sans contexte nommé, ses faits (échantillon acquis, connexion
perdue, flux en échec) seraient publiés sous des noms de la sonde de champ
électrique ou de l'ADC, et un futur détecteur de stabilité ne saurait pas à
quel sujet s'abonner.

## Responsibility

- Porter les événements domain du capteur inertiel : échantillon acquis,
  connexion changée, flux en échec (`events/`).

## Design

- **Pas d'agrégat à ce stade** : aucun invariant métier n'existe encore (le
  seuil de stabilité mécanique n'est pas décidé). Le dossier ne contient donc
  que des événements ; l'agrégat racine viendra avec la détection de
  stabilité, pas avant.
- Payloads en primitives et tuples, unités dans les noms (`_g`, `_dps`, `_ut`,
  `_mm`) et documentées en UCUM dans l'intention de chaque événement.
- Le mot « motion » est réservé aux moteurs d'AEFI ; l'acronyme du capteur
  n'est pas utilisé.
- **Dette non silencieuse** : le lidar mesure une distance, ce n'est pas un
  capteur inertiel. Il est un champ de l'événement d'échantillon parce qu'il
  voyage dans le même flux (même carte, même liaison série : considération
  d'infrastructure). À séparer : concept lidar distinct (voir
  `_system/ops/ponytail-debt.md`).
