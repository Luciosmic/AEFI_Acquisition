# i_acquisition_throughput_output_port — Intention

## Rationale

Un balayage dure de quelques dizaines de secondes à quelques minutes, hors
du thread UI. Sans port de sortie, l'opérateur ne verrait rien avant la fin
— ni la progression, ni qu'un point est aberrant — et un échec (scan en
cours, flux muet) se perdrait dans les logs.

## Responsibility

- `present_throughput_characterization_step(message)` : étape en cours.
- `present_throughput_point_measured(point)` : un point mesuré, affiché au fil
  de l'eau.
- `present_throughput_characterization_succeeded(result)` : résultat complet.
- `present_throughput_characterization_failed(reason)` : raison lisible.

## Design

- ABC pure, même patron que `ISensorCalibrationOutputPort` ; implémentée par
  `AcquisitionThroughputCharacterizationPresenter`, enregistrée via
  `set_output_port()`. Appelée depuis le thread de la tâche : thread-safe.
