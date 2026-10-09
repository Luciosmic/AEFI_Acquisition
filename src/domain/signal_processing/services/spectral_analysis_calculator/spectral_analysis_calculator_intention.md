# spectral_analysis_calculator — Intention

## Rationale

L'acquisition continue AEFI est cadencée par le round-trip FTDI/MCU, pas par une horloge ADC régulière (cf. `_system/documentation/adr/003_latency_budget_acquisition_chain.md`) : les échantillons arrivent à un intervalle moyen connu mais avec du jitter. Une FFT classique (`np.fft.rfft` direct sur la série brute) suppose un échantillonnage uniforme et produirait un spectre faussé sans réinterpolation préalable sur une grille temporelle régulière. Ce calcul est une règle de transformation mathématique pure, déterministe, sans effet de bord — elle appartient au domain, au même titre que `MeasurementStatisticsService`.

## Responsibility

- `compute(samples, window_duration_s) -> SpectralAnalysisResult` : réinterpoler une fenêtre d'échantillons (timestamp, valeurs par canal) sur une grille temporelle uniforme, appliquer une fenêtre de Hann, puis calculer le spectre d'amplitude (FFT réelle) par canal.

## Design

- Service stateless, méthode statique, aucune I/O — même patron que `MeasurementStatisticsService` (pas d'agrégat, pas d'invariant propre : une transformation mathématique n'a rien à refuser, elle retourne un résultat ou lève une erreur sur une entrée structurellement invalide, ex. moins de 2 échantillons).
- Prend des primitives (`Sequence[Tuple[datetime, Dict[str, float]]]`), pas directement `AefiCorrectedFieldMeasurement` : reste testable sans event bus ni dépendance au bounded context d'acquisition.
- Étapes (cf. pattern déjà validé dans `bruit_adc_50hz_secteur_characterization_test.py`) : (1) secondes relatives depuis le premier échantillon, (2) grille uniforme de pas = intervalle moyen mesuré, (3) interpolation linéaire (`np.interp`) par canal, (4) fenêtrage de Hann, (5) `np.fft.rfft`/`np.fft.rfftfreq`, (6) normalisation d'amplitude (`|fft| * 2 / somme(hanning)`).
