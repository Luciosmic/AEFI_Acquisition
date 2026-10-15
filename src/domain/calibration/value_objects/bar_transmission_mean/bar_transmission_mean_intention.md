# bar_transmission_mean — Intention

## Rationale

Le domaine garde une transmission commune aux axes X et Y (décision du
2026-10-15) : on écrit la moyenne des deux mesures. Mais une moyenne seule masquerait
un écart X/Y réel (poulies ou courroies différentes) qui justifierait un jour une
transmission par axe. Sans objet qui porte à la fois la moyenne et l'écart, l'écart
serait soit oublié, soit recalculé différemment par l'interface et par
l'enregistrement.

## Responsibility

- Combiner une mesure X et une mesure Y faites avec les mêmes réglages de chaîne
  (pas par tour, micro-pas) : moyenne `(T_X + T_Y) / 2` et son incertitude
  `(ΔT_X + ΔT_Y) / 2`.
- Donner l'écart `T_X − T_Y`, relatif à la moyenne, et dire si les deux axes sont
  compatibles (|écart| ≤ ΔT_X + ΔT_Y).

## Design

- Value object immuable. Refuse deux mesures du même axe, ou faites avec des
  réglages de chaîne différents (la moyenne n'aurait plus de sens).
- Même convention de bornes que `AxisBarTransmissionMeasurement`.
- L'écart est toujours exposé, jamais masqué : c'est à l'opérateur de juger.
