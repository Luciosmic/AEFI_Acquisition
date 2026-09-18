# i_synchronous_detection_phase_calibration_repository — Intention

## Rationale

Définir le contrat de persistance du registre de calibration de phase de
détection synchrone, suivant le pattern Repository DDD. Le domain déclare
QUOI persister (un registre append-only d'entrées, plus un flag de
compensation), l'infrastructure décide COMMENT (fichier JSON aujourd'hui,
cf. `RealSynchronousDetectionPhaseCalibrationRepository`).

## Responsibility

- `add(entry)` : ajouter une entrée au registre — **jamais** d'écrasement
  ni de suppression d'une entrée existante (registre constructif,
  append-only, décision actée avec l'utilisateur).
- `find_by_hardware_signature(signature)` : retrouver toutes les entrées
  enregistrées pour une signature matérielle donnée.
- `load_compensation_enabled()` : lire l'état persisté du flag de
  compensation — retourne `False` par défaut si aucun état n'a encore été
  sauvegardé.
- `save_compensation_enabled(enabled)` : persister le nouvel état du flag
  de compensation.

## Design

- **ABC placée dans `domain/calibration/repositories/`** : frontière
  domain/infrastructure pour la persistance de cet agrégat.
- Implémentée par `RealSynchronousDetectionPhaseCalibrationRepository`
  (JSON, `.aefi_acquisition/calibrations/synchronous_detection_phase_calibration.json`)
  et par `FakeSynchronousDetectionPhaseCalibrationRepository` (en mémoire)
  dans `infrastructure/persistence/calibration/`.
- L'interface domain ne connaît ni JSON ni chemin de fichier — le domain
  reste pur.
