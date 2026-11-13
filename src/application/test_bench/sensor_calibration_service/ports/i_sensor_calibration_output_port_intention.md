# i_sensor_calibration_output_port — Intention

## Rationale

La calibration automatique dure plusieurs secondes et tourne hors du thread
UI. Sans port de sortie, le presenter devrait sonder l'état du service pour
savoir où elle en est, ou l'opérateur resterait devant un bouton sans retour
— et un échec (niveau d'excitation nul, réponses dégénérées) passerait
inaperçu dans les logs.

## Responsibility

- `present_automatic_calibration_step(message)` : étape en cours (mesure
  baseline, excitation X, excitation Y).
- `present_automatic_calibration_succeeded(result)` : angles ajustés et
  qualité de l'ajustement ; les angles sont déjà appliqués comme essai.
- `present_automatic_calibration_failed(reason)` : raison lisible par
  l'opérateur.

## Design

- ABC pure, même patron que `IScanOutputPort` ; implémentée par
  `SensorCalibrationPresenter`, enregistrée via `set_output_port()`.
- Appelée depuis le thread de la tâche de fond : l'implémentation doit être
  thread-safe (signaux Qt).
