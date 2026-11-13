# i_adc_output_rate_output_port — Intention

## Rationale

Un balayage des 16 OSR prend quelques dizaines de secondes, hors du thread
UI. Sans port de sortie, l'opérateur ne verrait ni la progression, ni un OSR
qui n'est pas appliqué (f_MOD implicite aberrante), ni la raison d'un échec
(oscilloscope absent, lecture continue en cours).

## Responsibility

- `present_output_rate_step(message)`, `present_output_rate_point_measured(point)`,
  `present_output_rate_characterization_succeeded(result)`,
  `present_output_rate_characterization_failed(reason)`.

## Design

- ABC pure, même patron que `IAcquisitionThroughputOutputPort` ; implémentée
  par `AdcOutputRateCharacterizationPresenter`, thread-safe (signaux Qt).
