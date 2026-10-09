# aefi_point — Intention

## Rationale

Aujourd'hui les N échantillons ADC d'un point de step-scan sont collectés et moyennés dans la boucle du service applicatif, sans aucun invariant de domaine : un point acquis avec 3 échantillons au lieu de 10 ressemble à un point complet, ce qui signifie qu'une moyenne bruitée entre dans la cartographie sans que rien ne le refuse, ce qui force à auditer chaque carte après coup. L'atomicité physique de l'acquisition (N échantillons ou rien) est l'endroit où l'invariant fort doit vivre, pas le `Scan` (artefact de traçage fin).

## Responsibility

- Aggregate root d'un point de step-scan : identité `AefiPointId`, référence au scan par `scan_id` (identité seule), position, nombre attendu N d'échantillons.
- `record_samples(samples)` : accepte EXACTEMENT N `Sample` (valides par construction), atomiquement ; sinon `AefiPointIncompleteError` et aucun état modifié.
- Sur succès : calcule la mesure moyennée (via `MeasurementStatisticsService`) et empile `AefiPointAcquired`.
- Un point déjà acquis refuse un second enregistrement (`AefiPointAlreadyAcquiredError`).
- Expose `domain_events` (retourne puis vide la liste, convention de `StepScan`, requise par `IUnitOfWork.register`).

## Design

- Dataclass ; module d'agrégat à part entière (pas sous `step_scan/`, dont la racine porte déjà `StepScan`).
- Un point « en attente » (avant `record_samples`) n'est que la coquille de l'acquisition en cours ; le service l'ajoute au repository une fois acquis.
- Aucune logique de moyenne dupliquée : délégation à `MeasurementStatisticsService`.
- Domaine pur : aucun import infrastructure/application, aucun logger.
