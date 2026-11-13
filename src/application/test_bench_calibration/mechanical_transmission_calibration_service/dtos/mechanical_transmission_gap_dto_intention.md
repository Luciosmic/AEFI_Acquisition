# mechanical_transmission_gap_dto — Intention

## Rationale

Sans DTO de manque, `get_current_calibration() → None` ne dit pas pourquoi : le panneau ne peut qu'afficher « indisponible », et l'opérateur ne sait ni quelle grandeur saisir ni où.

## Responsibility

- Porter, en primitives, le moteur concerné, la grandeur manquante et l'endroit où la saisir.

## Design

- Construit par `MechanicalTransmissionCalibrationService.get_current_gap()` ; `None` quand la conversion est dérivable.
- Aucun objet domain ne traverse la frontière.
