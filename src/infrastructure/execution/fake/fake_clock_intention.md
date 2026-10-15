# fake_clock — Intention

## Rationale

La calibration par barre enchaîne un fly scan de butée à butée (plus d'une minute
au banc) et des dizaines d'attentes de stabilisation. En temps réel, ses tests
dureraient des minutes ; en supprimant le temps, les Fakes répondraient
instantanément et le fly scan ne verrait aucun échantillon LIDAR pendant le
mouvement : les tests passeraient sur un comportement que le banc n'a pas.

## Responsibility

- Fournir un temps virtuel partagé : `now()` et `sleep(durée)`, qui avance le temps
  sans attendre.

## Design

- Partagé entre le Fake du port moteur en incréments, le Fake du LIDAR (chaque
  lecture avance d'une période d'échantillonnage) et le service (horodatage et
  stabilisation) : les durées relatives restent celles du banc.
- Thread-safe (verrou) ; ne bloque jamais.
