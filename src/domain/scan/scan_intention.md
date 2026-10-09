# scan — Intention

## Rationale

Aujourd'hui `StepScan` contient ses points et se complète lui-même : il confond le processus physique avec son artefact de traçage, ce qui signifie qu'un agrégat gros et chargé de mesures porte la transaction de chaque point, ce qui force à tout verrouiller pour un seul point acquis. Le `Scan` est l'artefact qui dénote le processus : il référence ses points par identité et ne se complète que lorsqu'ils sont tous présents.

## Responsibility

- Aggregate root fin : identité `ScanId`, nombre de points attendus, ensemble des `AefiPointId` reçus.
- États PENDING (créé, observable) → STARTED (`start()`) → COMPLETED.
- `mark_point_acquired(id)` : idempotent (retourne False si déjà reçu) ; refusé avant start (`ScanNotStartedError`) et, pour un id inconnu, après complétion (`ScanAlreadyCompletedError`).
- COMPLETED seulement si tous les points attendus sont présents ; empile alors `ScanCompleted`.
- Expose `domain_events` (retourne puis vide, requis par `IUnitOfWork.register`).

## Design

- Coexiste avec `StepScan` (non modifié ; pause/cancel/failed non migrés).
- Réutilise `ScanCompleted` existant (forme `scan_id`, `total_points` adaptée). `ScanStarted` existant exige une config de scan : non réutilisé ni recréé (même nom de topic, forme différente) ; PENDING→STARTED reste observable par `state`.
- Domaine pur : aucun import application/infrastructure, aucun logger.
