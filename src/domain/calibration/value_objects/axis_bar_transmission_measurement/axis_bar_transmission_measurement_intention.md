# axis_bar_transmission_measurement — Intention

## Rationale

`travel_per_motor_revolution_mm` est la seule inconnue physique de la conversion
mm ↔ incréments : une erreur de x % sur elle est une erreur d'échelle de x % sur
toute la cartographie. Une mesure qui rendrait une transmission sans son
incertitude, ou sans les encadrements qui la justifient, ne permettrait pas à
l'opérateur de juger s'il faut l'enregistrer, ni de comparer X et Y. Et si le
calcul vivait dans le service applicatif, la propagation de l'incertitude (N, puis
L) ne serait testable qu'avec un banc.

## Responsibility

- Porter la mesure d'un axe : longueur L de la barre (et son incertitude, 0 si non
  fournie), les deux encadrements de fronts, et les réglages exacts de la chaîne
  (`full_steps_per_revolution`, `microsteps`).
- Calculer :
  - `N = |n₂ − n₁| ± (δ₁ + δ₂)`, avec `nᵢ = (aᵢ + bᵢ) / 2` et `δᵢ = |bᵢ − aᵢ| / 2` ;
  - `travel_per_motor_revolution_mm = L · full_steps_per_revolution · microsteps / N` ;
  - son incertitude, `ΔT / T = ΔL / L + ΔN / N`.

## Design

- Value object immuable, sans I/O.
- Incertitudes en **bornes** (demi-largeurs d'encadrement) additionnées
  linéairement, pas en quadrature : c'est la convention de `N ± (δ₁ + δ₂)` de la
  note de stratégie, et un encadrement est une borne, pas un écart-type. La
  propagation au premier ordre suit la même convention.
- L'axe est un libellé (« X », « Y ») : la mesure ne dépend pas de l'axe, seule
  la comparaison X/Y l'utilise.
