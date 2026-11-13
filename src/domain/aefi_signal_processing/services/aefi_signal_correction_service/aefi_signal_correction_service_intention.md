# aefi_signal_correction_service — Intention

## Rationale

L'algorithme de correction (soustraction de bruit, rotation de phase avec préservation de signe par quadrant, soustraction de champ primaire) vit aujourd'hui dans `SignalPostProcessor` (`interface/presenters/signal_processor.py`), une classe de la couche interface. C'est une règle métier pure et déterministe — aucune I/O, aucun état Qt — qui n'a rien à faire dans la couche interface, et qui doit pouvoir être appelée par l'agrégat `AefiCorrectedSample` sans dépendre de PySide6.

## Responsibility

- `apply(raw, calibration) -> AefiVoltageMeasurement` : applique dans l'ordre bruit → phase → champ primaire, uniquement pour les étapes activées dans `calibration`, et retourne une NOUVELLE mesure (jamais de mutation de `raw`).
- `calibrate_noise(current, calibration) -> AefiSignalCorrectionCalibration` : fige l'échantillon courant comme offset de bruit pour les 3 axes et active l'étape.
- `calibrate_phase(current_pre_phase, calibration) -> AefiSignalCorrectionCalibration` : calcule l'angle (`atan2(Q, I)`) à partir d'un échantillon déjà corrigé du bruit mais PAS encore de la phase, et active l'étape.
- `calibrate_primary(current_fully_processed, calibration) -> AefiSignalCorrectionCalibration` : fige l'échantillon courant (bruit + phase déjà appliqués) comme offset de champ primaire et active l'étape.

## Design

- Service stateless, méthodes statiques, aucune I/O — porté à l'identique depuis `signal_processor.py` lignes 29-138 (rotation avec préservation de signe par quadrant : le signe de `I` après rotation doit respecter le quadrant du vecteur `(I, Q)` d'origine, pas seulement l'algèbre de la rotation).
- Service interne à l'agrégat `AefiCorrectedSample` : la couche application ne l'appelle jamais directement, elle passe par l'agrégat.
- `calibrate_phase`/`calibrate_primary` ne lisent aucun état intermédiaire stocké : l'appelant doit lui-même recalculer l'échantillon intermédiaire (ex. `apply()` avec l'étape suivante désactivée) avant d'appeler — cf. `aefi_continuous_reading_presenter.py:133-147`, reproduit à l'identique.
- Clés d'axe `"x"`/`"y"`/`"z"`, alignées sur les champs nommés de `AefiVoltageMeasurement` (`voltage_x_in_phase`, etc.).
