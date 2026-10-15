# sample_rate_meter — Intention

## Rationale

La carte n'annonce pas sa cadence : le plafond de 25 Hz avec lidar, la
persistance de F entre sessions et la granularité d'horodatage du pilote USB
font que la cadence réelle n'est connue qu'en la mesurant. Sans mesure
affichée, l'opérateur ne distingue pas un flux à 25 Hz d'un flux à 3 Hz, ni un
flux sain d'un flux qui ralentit avant de tomber.

## Responsibility

- `SampleRateMeter(window_size)` : retient les `window_size` derniers
  horodatages (`timestamp_s`, secondes d'horloge monotone du PC, ceux de la
  réception) et donne la cadence en Hz sur cette fenêtre glissante.
- `rate_hz` : `None` sous 2 horodatages ou si l'intervalle est nul.
- `reset()`.

## Design

- Pure, sans Qt ni horloge : le temps vient des échantillons, pas de
  l'instant d'affichage (l'affichage est limité à ~10 Hz, la mesure ne doit
  pas en dépendre).
- Cadence = `(n - 1) / (dernier - premier)` : cadence moyenne sur la fenêtre,
  fiable à la granularité d'horodatage près (~16 ms observés).
- Aucune valeur métier : c'est une grandeur d'affichage de diagnostic.
