# acquisition_throughput_analysis — Intention

## Rationale

Sans ce service, chaque balayage de `n_avg` produit une pile d'échantillons
horodatés que l'opérateur doit dépouiller à la main (tableur, script
ad hoc) — c'est ce qui s'est passé en 2024 et le résultat a été perdu. Les
règles de dépouillement (comment calculer la période, quel critère de
bruit, quel `n_avg` retenir) doivent vivre au même endroit que le reste du
domaine de calibration pour que deux caractérisations soient comparables.

## Responsibility

- `characterize_point(n_avg, sample_periods_s, channel_samples_v)` :
  période moyenne, débits, σ par voie (écart-type échantillon, ddof=1),
  bruit atteignable en 1 s `σ_rms · √période` (avec `σ_rms` la moyenne
  quadratique des σ des 6 voies).
- `characterize_acquisition_throughput(points)` : ajustement linéaire
  `T(n) = T₀ + n/ODR` (moindres carrés), écart relatif max au modèle, et
  `n_avg` recommandé.

## Design

- **Critère de choix** : le bruit atteignable en 1 s. Il combine débit et
  moyennage : `K = 1/T` échantillons par seconde de bruit `σ` donnent
  `σ/√K = σ·√T`. Le `n_avg` recommandé est le plus petit dont ce bruit est à
  moins de `NOISE_IN_ONE_SECOND_TOLERANCE` (5 %) du meilleur — au-delà, monter
  `n_avg` ne fait que ralentir la cadence de sortie. 5 % est un bouton de
  réglage, pas une loi.
- **Incertitude statistique** : σ estimé sur N échantillons est connu à
  `1/√(2(N−1))` près (10 % à N = 51). Elle est rendue
  (`noise_relative_uncertainty`, pire point) : deux `n_avg` dont le bruit en
  1 s diffère de moins que cela ne sont pas départagés, et la recommandation
  peut basculer d'une mesure à l'autre (vu en mock : 64 ↔ 127 à N = 20).
- `T₀` et `ODR` interprètent la droite : `ODR` = cadence réelle de l'ADC
  (sans connaître le quartz), `T₀` = coût fixe d'un aller-retour (série,
  Python). Une pente qui pèse moins de `MIN_RESOLVABLE_SLOPE_SHARE` (1 %) de
  la période au plus grand `n_avg` est de la gigue de timing, pas l'ADC :
  `ODR = None`, le coût fixe écrase tout. L'écart relatif max signale une courbe non linéaire.
- Entrées invalides (moins de 2 échantillons, période non positive, moins de
  2 `n_avg` distincts) : `ValueError` — erreur de programmation, l'appelant
  garantit ces conditions.
- Fonctions pures, numpy uniquement, pas d'I/O.
