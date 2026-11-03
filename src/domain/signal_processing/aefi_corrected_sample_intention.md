# aefi_corrected_sample — Intention

## Rationale

Aujourd'hui, la correction de signal (bruit/phase/primaire) est une fonction sans garde-fou : `self.state.phase_angles.get(axis, 0.0)` (`interface/presenters/signal_processor.py`) retourne silencieusement 0.0 si une correction est activée sans être calibrée, ce qui signifie qu'un échantillon "corrigé" peut sortir du pipeline alors que la calibration est incomplète — sans qu'aucune erreur ne le signale, sans qu'aucun log ne le trace. En comparant au pattern déjà présent dans ce repo pour `AefiPoint` (`domain/aefi_point/aefi_point.py`), qui refuse un point avec un nombre d'échantillons incorrect via `AefiPointIncompleteError` plutôt que d'accepter une moyenne bruitée, la bonne modélisation est un agrégat qui REJETTE la correction si une étape activée n'a pas de calibration complète pour les 3 axes, plutôt qu'une fonction pure qui comble silencieusement le vide avec un offset nul.

## Responsibility

- Construire, via `correct(raw, calibration, acquisition_id, sample_index)`, un échantillon corrigé à partir d'une mesure brute et d'un instantané de calibration.
- Valider l'invariant AVANT toute correction : si une étape (bruit, phase, primaire) est activée sans offset/angle renseigné pour les 3 axes, lever `SignalCorrectionCalibrationMissingError` — aucun état n'est créé, aucun event n'est émis.
- Sur succès : déléguer le calcul à `AefiSignalCorrectionService.apply` et empiler `AefiSampleCorrected`.
- Exposer `domain_events` (retourne puis vide la liste, convention de `StepScan`/`AefiPoint`).

## Design

- Dataclass ; module d'agrégat à part entière sous `domain/signal_processing/` (pas `shared_kernel/` — ces concepts ne sont utilisés que par ce flux, cf. standard shared-domain-concept-extraction du repo).
- Pas d'ID dédié ni de repository : contrairement à `AefiPoint`, rien ici n'est persisté entre deux appels — la construction valide via `correct()` est le seul état qui compte, un `AefiCorrectedSample` existe toujours dans un état "corrigé avec succès" (pas d'état "en attente" comme `AefiPoint` avant `record_samples`).
- L'event `AefiSampleCorrected` n'est émis qu'après validation de l'invariant (cohérent avec le standard EventStore du repo : "émettre un domain event uniquement depuis l'Aggregate Root, après validation de l'invariant").
- Un rejet d'invariant ne produit pas de domain event (cohérent avec le standard EventStore : "un rejet d'invariant domain ne produit pas de domain event, il produit un log structuré") — le log est de la responsabilité de l'appelant applicatif, pas de l'agrégat (le domain est pur, sans logger).
- Domaine pur : aucun import infrastructure/application, aucun logger.
