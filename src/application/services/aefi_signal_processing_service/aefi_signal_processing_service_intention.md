# aefi_signal_processing_service — Intention

## Rationale

Avant ce service, la correction de signal (bruit/phase/primaire) était exécutée directement par `interface/presenters/aefi_continuous_reading_presenter.py` via `SignalPostProcessor`, sans invariant : une correction activée sans calibration retournait silencieusement un offset nul. L'agrégat `AefiCorrectedSample` (`domain/signal_processing/`) porte maintenant cet invariant et rejette la correction incomplète — mais un agrégat domain ne s'abonne pas lui-même à un event bus et ne republie pas d'events : il faut une couche applicative qui réagit à chaque échantillon brut, invoque l'agrégat, et republie ce qu'il produit, sans dupliquer son invariant ni le contourner.

## Responsibility

- S'abonner à `aefivoltagesampleacquired` et, pour chaque échantillon : appeler `AefiCorrectedSample.correct(...)` avec la calibration courante.
- Sur rejet (`SignalCorrectionCalibrationMissingError`) : logger un warning avec les IDs métier (acquisition_id, sample_index) et ne rien publier pour cet échantillon — l'échantillon est simplement absent du flux corrigé pour ce tour (cohérent avec le standard EventStore : un rejet d'invariant ne produit pas de domain event).
- Sur succès : republier les `domain_events` de l'agrégat (`AefiSampleCorrected`), puis enchaîner `TransformationService.transform_sensor_to_source` (réutilisé tel quel, non modifié) sur les vecteurs In-Phase et Quadrature pour produire un `AefiCorrectedFieldMeasurement`, et publier `AefiCorrectedFieldSampleAcquired`.
- Exposer les commandes de calibration (`calibrate_noise`, `calibrate_phase`, `calibrate_primary`, `reset_calibration`, `set_*_correction_enabled`) qui mutent `self._calibration` (nouvelle instance immuable à chaque fois) puis publient `AefiSignalCorrectionCalibrationUpdated`.
- Exposer la query `get_calibration()`.

## Design

- `calibrate_phase`/`calibrate_primary` n'appellent jamais l'agrégat `AefiCorrectedSample` — ce n'est pas une correction d'échantillon mais un calcul de calibration, qui appelle directement le domain service `AefiSignalCorrectionService` (interne à l'agrégat pour `correct()`, mais la calibration passe par lui explicitement ici, comme documenté dans `aefi_signal_correction_service_intention.md`).
- `calibrate_phase` recalcule l'échantillon intermédiaire pré-phase à la volée depuis `self._last_raw_sample`, avec une calibration temporaire où seule l'étape phase est désactivée (bruit/primaire inchangés) — reproduit à l'identique le comportement vérifié de `aefi_continuous_reading_presenter.py` (avant refactoring) et `signal_processor.py`.
- `calibrate_primary` applique la calibration courante complète (bruit + phase si activés) à `self._last_raw_sample` avant de calculer l'offset primaire — même comportement que l'ancien presenter.
- Logger nommé `logging.getLogger(__name__)` (standard logs-driven-design du repo).
- Pas de `ports/` : seuls `IDomainEventBus` et `TransformationService` sont injectés, aucune I/O propre à ce service.
