# adc_output_rate_characterization — Intention

## Rationale

Sans objet qui porte une mesure d'ODR avec sa dispersion et le nombre
d'intervalles écartés, une valeur « 1000 Hz » ne dit ni sur combien de
périodes elle repose, ni si des impulsions ont été perdues ; et une courbe
ODR(OSR) sans `f_MOD` implicite ne dit pas si l'ADC a appliqué chaque OSR.

## Responsibility

- `AdcOutputRateMeasurement` : un OSR, le nombre d'intervalles réguliers et
  irréguliers, l'intervalle médian, la moyenne et l'écart-type des intervalles
  réguliers, l'ODR, la `f_MOD` implicite.
- `AdcOutputRateCharacterization` : les mesures triées par OSR décroissant,
  la `f_MOD` moyenne et l'écart relatif maximal des `f_MOD` implicites.

## Design

- `@dataclass(frozen=True)`, unités SI, aucune logique : construits et testés
  via `services/adc_output_rate_analysis/`.
