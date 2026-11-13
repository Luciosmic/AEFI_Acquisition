---
type: evenement-de-domaine::solidai-ddd
tldr: "Fait passé : un échantillon corrigé (bruit/phase/primaire) a été transformé du repère capteur vers le repère sources."
code: ["[[src/domain/aefi_signal_processing/events/aefi_corrected_field_sample_acquired/aefi_corrected_field_sample_acquired.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/aefi_signal_processing/aefi_corrected_sample_intention]]"
---
# aefi_corrected_field_sample_acquired — Intention

## Rationale

Sans fait publié après la transformation repère capteur → repère sources, les deux consommateurs du signal corrigé transformé (le plot temporel existant et la future FFT) ne pourraient partager ce résultat qu'en recalculant chacun `TransformationService.transform_sensor_to_source`, dupliquant la logique d'orchestration à chaque endroit.

## Responsibility

- Fait passé : un échantillon corrigé (bruit/phase/primaire) a été transformé du repère capteur vers le repère sources.
- Porte l'identifiant d'acquisition, l'index de l'échantillon et la mesure transformée (`AefiCorrectedFieldMeasurement`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par la couche application (orchestration : agrégat + `TransformationService`), pas par l'agrégat `AefiCorrectedSample` lui-même — la transformation de repère n'est pas un invariant du signal corrigé. Topic : `"aeficorrectedfieldsampleacquired"`.
- C'est l'event auquel `SpectralAnalysisService` s'abonne pour alimenter la FFT (signal déjà corrigé, pas le brut).
