# aefi_sample_corrected — Intention

## Rationale

Sans fait publié à la correction d'un échantillon, un second consommateur (la future FFT) ne pourrait partager le signal corrigé par le plot temporel qu'en dupliquant l'appel à `AefiSignalCorrectionService`, ou en lisant un état mutable partagé — ce qui recrée le couplage que ce bounded context est censé éliminer.

## Responsibility

- Fait passé : un échantillon brut a été corrigé (bruit/phase/primaire selon les étapes activées), avec succès — l'invariant de calibration complète est déjà validé au moment de l'émission.
- Porte l'identifiant d'acquisition, l'index de l'échantillon et la mesure corrigée, encore dans le repère capteur (pas encore transformée vers le repère sources).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par `AefiCorrectedSample.correct` uniquement, après validation de l'invariant (cohérent avec le standard EventStore du repo). Topic : `"aefisamplecorrected"`.
- Un rejet d'invariant (calibration incomplète) ne produit PAS cet event — seulement un `SignalCorrectionCalibrationMissingError` levé.
