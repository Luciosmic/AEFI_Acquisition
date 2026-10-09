# narda_point — Intention

## Rationale

Aujourd'hui la mesure de champ électrique d'un point de scan est moyennée et publiée directement sur le bus par le canal de sonde, hors agrégat et hors transaction : une fenêtre à 3 échantillons au lieu de 10 passe pour un point complet, ce qui signifie qu'une moyenne bruitée entre dans la cartographie de champ, et que le `Scan` ne peut pas savoir si ses mesures de champ sont complètes. L'atomicité physique (N échantillons, plus N de baseline en mode différentiel, ou rien) est l'endroit où l'invariant fort doit vivre.

## Responsibility

- Aggregate root d'un point de champ électrique : identité `NardaPointId`, référence au scan par `scan_id`, `point_index` (clé de corrélation avec le point AEFI et l'affichage), position, N attendu, `expects_baseline`, libellés d'axes.
- `record_samples(samples, baseline_samples=None)` : EXACTEMENT N `FieldMeasurement` ; si `expects_baseline`, exactement N de baseline, sinon aucune ; sinon `NardaPointIncompleteError` et aucun état modifié.
- Sur succès : calcule les mesures moyennées (via `FieldMeasurementStatisticsService`) et empile `NardaPointAcquired`.
- Un point déjà acquis refuse un second enregistrement (`NardaPointAlreadyAcquiredError`).
- Expose `domain_events` (retourne puis vide, requis par `IUnitOfWork.register`).

## Design

- Dataclass ; même forme que `AefiPoint`, mais `point_index` est porté (l'export et l'UI corrèlent par index).
- Aucune logique statistique dupliquée : délégation au service existant.
- Domaine pur : aucun import infrastructure/application, aucun logger.
