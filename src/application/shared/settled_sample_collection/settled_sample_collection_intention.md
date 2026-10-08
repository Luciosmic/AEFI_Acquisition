# settled_sample_collection — Intention

## Rationale

Chaque fois qu'un service change une condition de mesure (excitation,
`n_avg`…) puis lit le flux ADC, des échantillons acquis sous l'ancienne
condition sont encore en transit (tampon série/USB, abonné lent sur le bus).
« Vider la file puis jeter le premier » suppose un seul échantillon en
transit : faux dès qu'il y en a plusieurs, et silencieux. Écrite une fois
dans la calibration capteur, la règle robuste aurait été recopiée dans la
caractérisation du débit — deux copies d'un même invariant divergent.

## Responsibility

- `collect_settled_samples(events, count, settled_at, timeout_s)` : lire la
  file d'événements `AefiVoltageSampleAcquired` et ne garder que ceux dont
  l'acquisition a commencé après `settled_at`. Rend les événements gardés
  (dans l'ordre) et le nombre rejeté ; s'arrête à `count` ou au délai.

## Design

- **Règle causale** : l'horodatage d'un échantillon marque la FIN de sa
  fenêtre d'acquisition (pris à la réponse du MCU), et le flux acquiert
  sans pause : l'échantillon i commence après la fin de i−1. On garde i ssi
  son prédécesseur immédiat (même `acquisition_id`, index i−1) s'est
  terminé après `settled_at` — quel que soit le nombre d'échantillons en
  transit.
- Les événements gardés sont consécutifs : les écarts d'horodatage entre
  gardés successifs sont les durées d'aller-retour (utilisé par la
  caractérisation du débit).
- Fonction, pas de classe : aucun état à garder entre deux appels.
- Rend une collecte éventuellement incomplète ; l'appelant décide si c'est
  un échec.
