# spectral_analysis_result_updated — Intention

## Rationale

Sans fait publié à chaque nouveau spectre calculé, le futur dock FFT ne pourrait se mettre à jour qu'en interrogeant activement le service applicatif, ce qui romprait le patron "subscribe dans `__init__`, calcul, publish" déjà établi dans ce repo (ex. `AefiVoltageSampleAcquired` → `AefiContinuousReadingPresenter`).

## Responsibility

- Fait passé : un nouveau résultat d'analyse spectrale a été calculé pour la fenêtre courante d'une acquisition.
- Porte l'identifiant d'acquisition et le résultat (`SpectralAnalysisResult`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par `SpectralAnalysisService` (couche application) après chaque recalcul (une fois la fenêtre pleine). Topic : `"spectralanalysisresultupdated"`.
