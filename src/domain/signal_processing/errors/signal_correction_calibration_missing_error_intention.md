# signal_correction_calibration_missing_error — Intention

## Rationale

Sans erreur nommée, une étape de correction activée sans calibration complète est aujourd'hui absorbée en silence : `self.state.phase_angles.get(axis, 0.0)` (`interface/presenters/signal_processor.py`) retourne 0.0 par défaut, produisant un échantillon "corrigé" qui ne l'est pas vraiment, sans qu'aucune erreur ne le signale. Sans erreur nommée distincte, l'appelant ne pourrait pas non plus distinguer ce rejet métier d'un `ValueError` anonyme ou d'un bug.

## Responsibility

- Nommer la promesse refusée : « une étape de correction (bruit, phase ou champ primaire) activée exige une calibration pour les 3 axes avant d'être appliquée ».

## Design

- Hérite de `ValueError` (convention `AefiPointIncompleteError`) ; porte l'étape concernée (`stage`) et la calibration incomplète.
