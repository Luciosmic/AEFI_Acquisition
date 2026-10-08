# adc_output_rate_analysis — Intention

## Rationale

La cadence de sortie de l'ADC (ODR) fixe tout ce qui en dépend : le temps
d'un moyennage MCU de `n_avg` conversions, les zéros du filtre de moyennage
(un brouillage à 50 Hz s'annule si `n_avg/ODR` couvre un nombre entier de
périodes), la grandeur « cadence » du catalogue ADC. Calculée depuis
l'horloge (`f_CLKIN / (CLK_DIV·ICLK_DIV·OSR)`), elle repose sur une fréquence
d'horloge qui n'est consignée nulle part ; ajustée sur le temps
d'aller-retour T(n), elle s'est trompée de −1,9 % à +2,7 % le 2026-10-02.
Seule la broche DRDY (une impulsion par conversion, datasheet SBAS590E
§9.3.1) la donne sans hypothèse. Sans règles de dépouillement fixées ici,
chaque mesure redécide quels intervalles garder et la courbe ODR(OSR) n'est
pas comparable d'une fois sur l'autre.

## Responsibility

- `measure_output_rate(oversampling_ratio, falling_edge_times_s)` : à partir
  des instants des fronts descendants de DRDY, les intervalles consécutifs,
  l'intervalle médian, la moyenne et l'écart-type des intervalles « réguliers »
  (à moins de `REGULAR_INTERVAL_TOLERANCE` de la médiane), l'ODR = 1/moyenne,
  et la fréquence de modulateur implicite `f_MOD = ODR × OSR`.
- `characterize_output_rate(measurements)` : sur plusieurs OSR, la moyenne
  des `f_MOD` implicites et leur écart relatif maximal à cette moyenne —
  si l'ADC applique bien chaque OSR, `f_MOD` est le même pour tous
  (`f_DATA = f_MOD / OSR`, datasheet §9.3.1.4).

## Design

- Intervalles « réguliers » : à moins de 5 % de la médiane. Un intervalle
  plus long (pause, impulsion manquée) n'est pas une période et reste compté
  à part (`irregular_interval_count`), jamais silencieusement mélangé. 5 % est
  un bouton de réglage, pas une loi.
- Moins de 2 fronts, ou aucun intervalle régulier : `ValueError` — l'appelant
  vérifie la capture avant (erreur de programmation sinon).
- Fonctions pures, numpy, pas d'I/O ; testées avec des fronts synthétiques.
